# Chapter 2 — The Canadian Space Ecosystem and Regulatory Environment

> **Recommended background.** NASA Systems Engineering Handbook §4.1 (stakeholder expectations); SMAD4 Ch. 1 (mission objectives); the Canadian statutes listed in the References, in particular the Remote Sensing Space Systems Act and the Radiocommunication Act. This chapter builds on the lifecycle phases and review gates of Chapter 1.

## Learning objectives

By the end of this chapter, you will be able to:

1. Describe the Canadian Space Agency's mandate and organisational structure
2. Map the Canadian space industry ecosystem — prime contractors, SMEs, universities, and funding programmes
3. Identify the regulatory bodies that govern space activities in Canada (CSA, ISED, GAC, DND)
4. Explain the RSSSA licensing process for remote sensing satellites
5. Describe the spectrum licensing process through ISED and ITU coordination
6. Identify Canadian export control obligations under EIPA, ITAR, and EAR

---

## 2.1 The Canadian Space Agency

### 2.1.1 Mandate and history

The Canadian Space Agency (CSA) was established by the *Canadian Space Agency Act* (S.C. 1990, c. 13) with the mandate to "promote the peaceful use and development of space, to advance the knowledge of space through science and to ensure that space science and technology provide social and economic benefits for Canadians."

| Milestone | Year | Significance |
|-----------|------|-------------|
| Alouette 1 | 1962 | Canada becomes the 3rd nation to build and design a satellite |
| Hermes (CTS) | 1976 | World's first high-power direct broadcast satellite (CSA/NASA) |
| Canadarm | 1981 | Robotic arm for Space Shuttle; established Canada's space robotics dominance |
| CSA established | 1990 | Canadian Space Agency Act creates the agency |
| RADARSAT-1 | 1995 | First Canadian Earth observation satellite; C-band SAR |
| Canadarm2 | 2001 | ISS robotic arm; continues robotics legacy |
| RADARSAT-2 | 2007 | Commercial SAR satellite (MDA); RSSSA applies |
| RADARSAT Constellation Mission (RCM) | 2019 | Three C-band SAR satellites; maritime surveillance, disaster management |
| Lunar Gateway participation | 2019–2026 | Canada committed as partner; in March 2026 NASA paused Gateway "in its current form" (widely reported as a cancellation) in favour of a lunar surface base |
| Canadarm3 | In development | Next-generation autonomous robotics begun for the Lunar Gateway; as of late 2026 being repurposed by the CSA for lunar-surface operations under Artemis |

[Source: CSA, "Canada's Space Milestones", www.asc-csa.gc.ca; Gateway and Canadarm3 status as of late 2026 from References 12–13]

### 2.1.2 CSA organisational focus areas

The CSA is headquartered in Saint-Hubert, Quebec, and organises its activities around three strategic priorities:

| Priority | Activities | Key programmes |
|----------|-----------|-------------|
| **Space Exploration** | ISS operations, Artemis lunar exploration (Canadarm3 technologies repurposed for lunar-surface operations), astronaut programme | Lunar Exploration Accelerator Program (LEAP) |
| **Space Utilisation** | Earth observation, satellite communications, GNSS augmentation | RADARSAT, SmartEarth, eHealth |
| **Space Science and Technology** | Astronomy, planetary science, technology development | CASTOR, JWST/NIRISS, space health |

### 2.1.3 Canadian Space Strategy (2019)

*Exploration, Imagination, Innovation: A New Space Strategy for Canada* (2019) committed $2.05B over 24 years and established five priorities:

1. Ensure astronaut health and well-being in deep space
2. Develop and use advanced AI and robotics in space
3. Connect rural and remote Canadians through next-generation satellite communications
4. Use space data and technology to manage natural resources sustainably
5. Position the Canadian space sector for the future

> **Industry practice.** The $150M Lunar Exploration Accelerator Program (LEAP) specifically targets Canadian SMEs and universities to develop technologies for lunar surface science, health, AI, and robotics. This "pull-through" model — where a strategic government investment creates opportunities for industry — is a hallmark of the Canadian space ecosystem.

---

## 2.2 Canadian space industry map

### 2.2.1 Industry structure

The Canadian space industry generated approximately $2.7B in revenue (2022) and employs ~12,000 people. It is structured in tiers, and a representative map of the organisations a Canadian mission interacts with is shown in Figure 2.1.

![Representative stakeholder map for Canadian space missions: agency, primes, subsystem suppliers, SMEs, academia and regulators.](../assets/figures/fig_canadian_sector.png)

**Figure 2.1** — Representative stakeholder map for Canadian missions: the agency and funding bodies, the industry tiers, academia and the regulators that a mission must engage.

| Tier | Role | Key players | Revenue share |
|------|------|-------------|--------------|
| **Tier 1: Primes** | System integration, large platforms, constellation operations | MDA Space, Telesat, SFL (U of T) | ~60 % |
| **Tier 2: Subsystem/Component** | Subsystem design, specialised components, ground systems | Honeywell Canada, ABB, Magellan Aerospace, NGC Aerospace | ~25 % |
| **Tier 3: SMEs and Startups** | Niche technologies, applications, data analytics | GHGSat, NorthStar, Kepler Communications, Wyvern | ~10 % |
| **Tier 4: Academia** | R&D, training, technology incubation | U of T (SFL), York U, UBC, U of Calgary, Western | ~5 % |

Company names in this chapter are representative examples, not endorsements.

### 2.2.2 Key Canadian space capabilities

Canada has world-leading capabilities in several domains:

| Capability | Key player(s) | Notable missions | Global standing |
|-----------|--------------|-----------------|----------------|
| **Space robotics** | MDA Space | Canadarm, Canadarm2, Dextre, Canadarm3 | World leader |
| **SAR Earth observation** | MDA Space, CSA | RADARSAT-1/2/RCM | Top 3 globally |
| **Satellite communications** | Telesat | Anik fleet, Telesat Lightspeed (LEO constellation) | Pioneer in GEO DBS |
| **Small satellite systems** | SFL (U of T) | MOST, NEOSSat, GHGSat-D, BRITE | Top university lab globally |
| **GHG monitoring** | GHGSat | GHGSat constellation (methane) | World's only commercial GHG monitoring constellation |
| **Optical instruments** | ABB, Honeywell | JWST/FGS-NIRISS, OSIRIS-REx laser altimeter | Tier 1 instrument builder |
| **Star trackers/AOCS** | NGC Aerospace/Honeywell | Numerous missions | Widely used sensors |

### 2.2.3 Funding programmes

Canadian space activities are funded through several mechanisms (values indicative, 2026):

| Programme | Administered by | Scope | Typical value |
|---------|----------------|-------|--------------|
| **Space Technology Development Program (STDP)** | CSA | TRL advancement for flight heritage | $100K–$3M per project |
| **Class Grants and Contributions** | CSA | Space science, awareness, STEM | Variable |
| **LEAP** | CSA | Lunar technology development | Up to $3M per project |
| **IRAP** | NRC | SME innovation support | $50K–$1M |
| **SIF** | ISED | Strategic innovation projects | $10M–$100M+ |
| **DRDC contracts** | DND | Dual-use technology | Classified–$10M |
| **NSERC / CFI** | Federal | Academic research infrastructure | $50K–$5M |

> **Industry practice.** GHGSat (Montreal) progressed from a CSA-funded technology demonstrator (GHGSat-D "Claire", launched 2016) to a commercial constellation of 12+ satellites monitoring methane emissions from individual industrial facilities. This trajectory — government seed funding enabling commercial scale-up — is the canonical Canadian space industry growth model.

---

## 2.3 Comparison with other national models

Understanding Canada's space ecosystem requires comparing it with partner agencies:

| Parameter | Canada (CSA) | USA (NASA) | Europe (ESA) | Japan (JAXA) |
|-----------|-------------|-----------|-------------|-------------|
| Annual budget (approx.) | ~$300M CAD | ~$25B USD | ~€7.5B | ~$1.5B USD |
| Staff | ~670 | ~18,000 | ~2,300 | ~1,500 |
| Launch capability | None (uses partners) | SLS, commercial (SpaceX, ULA) | Ariane 6, Vega-C | H3, Epsilon |
| Key strength | Robotics, SAR, instruments | Full spectrum | Science, EO, navigation | Rockets, science, ISS (Kibo) |
| Industry model | Government seed + commercial scale | Government prime + commercial | *Juste retour* (geographic return) | Government-led + commercial |

Canada's lack of indigenous launch capability means all Canadian satellites launch on foreign vehicles, which has implications for export control (§2.8).

---

## 2.4 Canadian space in the international context

### 2.4.1 International partnerships

Canada participates in space through multilateral and bilateral agreements:

| Partnership | Canadian contribution | Canadian benefit |
|------------|----------------------|-----------------|
| **ISS** | Canadarm2, Dextre, SPDM | Astronaut access, research time, technology demonstrations |
| **Artemis** (Lunar Gateway until its March 2026 pause) | Canadarm3, repurposed for lunar-surface operations (2026) | Astronaut flights, lunar science access |
| **Copernicus (ESA)** | Data access agreement | Free access to Sentinel data for Canadian users |
| **COSPAS-SARSAT** | Canadian ground stations, MEOSAR payloads | Search and rescue capability for Canadian territory |
| **Five Eyes** | Intelligence sharing, dual-use technology | Access to allied space intelligence capabilities |

### 2.4.2 The Canadian niche strategy

Canada has historically pursued a "niche excellence" strategy: rather than attempting full-spectrum space capability, Canada develops world-class expertise in specific domains (robotics, SAR, instruments) and trades access to these capabilities for partnership in larger programmes.

> **Key equation.** The "partnership leverage ratio" — informal but useful — describes how Canada trades capability for access:
>
> $$L = \frac{V_{\text{access}}}{C_{\text{contribution}}}$$
>
> where $V_{\text{access}}$ is the value of programme access obtained and $C_{\text{contribution}}$ is the cost of Canada's contribution. For the ISS, Canada's Canadarm2/Dextre contribution (~\$2B CAD over 30 years) provides access to a \$150B+ programme, yielding $L \approx 75$. This is the highest leverage ratio of any ISS partner.

---

## 2.5 Regulatory framework overview

Space activities in Canada are governed by multiple federal bodies. There is no single "Space Act" — instead, regulation is distributed across several statutes. Figure 2.2 shows the bodies a single space activity must satisfy and the statute each one administers; the table below gives the detail.

![Canadian space regulatory framework: a central space-activity node connected to the five federal regulators and three international bodies.](../assets/figures/fig_regulatory_framework.png)

**Figure 2.2** — The Canadian space regulatory framework. A single space activity is regulated by five federal bodies under separate statutes (CSA, ISED, GAC, DND/DRDC and, for launch, Transport Canada in future), while the international instruments of the ITU, UN COPUOS and the MTCR reach the mission through ISED, treaty obligations and the Export Control List administered by GAC.

| Regulatory body | Statute | What it regulates | Relevance to mission design |
|----------------|---------|-------------------|---------------------------|
| **CSA** | Canadian Space Agency Act | Space programme coordination, policy | Mission approval, funding |
| **ISED** | Radiocommunication Act | Radio spectrum allocation, licensing | Frequency licensing for all RF transmissions |
| **ISED** | Remote Sensing Space Systems Act (RSSSA) | Operation of remote sensing satellites | Licensing for any satellite that images Earth |
| **GAC** | Export and Import Permits Act (EIPA) | Export control of strategic goods | Export permits for satellite technology |
| **GAC** | Controlled Goods Program | Access to controlled (ITAR/CG) goods | Personnel security clearances |
| **DND/DRDC** | National Defence Act | Dual-use technology, military space | Classification, security requirements |
| **Transport Canada** | (No current statute) | Launch operations (future) | Canada has no domestic launch regulation yet |

---

## 2.6 Remote Sensing Space Systems Act (RSSSA)

### 2.6.1 Purpose and scope

The RSSSA (S.C. 2005, c. 45) regulates the operation of remote sensing satellites from Canada. It was enacted primarily in response to the commercialisation of RADARSAT-2 (the first Canadian commercial EO satellite) and addresses national security and foreign policy concerns related to Earth imagery.

[Source: Government of Canada, RSSSA, https://laws-lois.justice.gc.ca/eng/acts/r-5.4/]

### 2.6.2 Who needs a licence?

An RSSSA licence is required for any person or entity that:

- **Operates** a remote sensing space system from Canada, or
- **Controls** the collection or distribution of remote sensing data from a Canadian system

This applies regardless of where the satellite is manufactured or launched. If it is operated from Canadian soil, RSSSA applies.

### 2.6.3 Licence categories and conditions

| Licence type | Scope | Typical conditions |
|-------------|-------|-------------------|
| **System Operating Licence** | Operate a remote sensing satellite system | Data handling plan, priority access for Canadian government, shutter control provisions |
| **Interoperability Arrangements** | Share data with foreign entities | Approval for each foreign government or commercial partner |

Key conditions typically imposed:

| Condition | Description | Rationale |
|-----------|-------------|-----------|
| **Priority access** | Government of Canada can request priority imaging of any area | National security |
| **Shutter control** | Government can restrict imaging of specified areas | National security, diplomatic relations |
| **Data disposition** | Approved plan for data storage, distribution, and destruction | Prevent unauthorised access |
| **System disposal** | Plan for end-of-life decommissioning | Space debris mitigation |
| **Raw data protection** | Restrictions on distribution of unprocessed data | Prevent circumvention of controls |

### 2.6.4 Implications for CubeSat and university missions

Even small CubeSat missions with cameras must comply with RSSSA if they produce images of Earth. Key considerations:

| Parameter | Threshold | Implication |
|-----------|-----------|------------|
| GSD | No formal threshold in the Act | All resolutions require licensing |
| Orbit type | Any orbit imaging Earth | LEO, MEO, GEO all in scope |
| Data distribution | Any distribution of imagery | Must have approved data handling plan |
| Foreign participation | Any foreign access to data | Requires interoperability arrangement |

> **Industry practice.** MDA's RADARSAT-2 operates under an RSSSA licence that includes shutter control provisions. During the 2010 Haiti earthquake response, the Government of Canada exercised priority access to direct RADARSAT-2 to image the disaster zone within hours. This demonstrates both the operational utility and the regulatory mechanism of RSSSA.

---

## 2.7 Spectrum management and licensing

### 2.7.1 Why spectrum licensing matters

Every satellite that transmits or receives radio signals requires spectrum authorisation. This is not optional — unauthorised RF transmission is illegal in all ITU member states and can result in harmful interference to other systems.

The process involves two levels:

1. **National:** ISED (Innovation, Science and Economic Development Canada) issues the radio licence
2. **International:** ITU (International Telecommunication Union) coordinates the frequency filing to prevent interference with other national administrations

### 2.7.2 The ITU framework

The International Telecommunication Union allocates spectrum globally through the Radio Regulations (RR), updated at World Radiocommunication Conferences (WRC) every 3–4 years.

| ITU concept | Description | Relevance |
|-------------|-------------|-----------|
| **Frequency allocation** | Spectrum divided among radio services (Fixed Satellite, Mobile, Earth Exploration Satellite, etc.) | Determines which bands are available for a given mission type |
| **ITU Regions** | Region 1 (Europe/Africa), Region 2 (Americas), Region 3 (Asia/Pacific) | Canada is in Region 2; allocations may differ by region |
| **Coordination** | Bilateral/multilateral agreements to avoid interference | Required before a new satellite system can operate |
| **Notification** | Formal filing with the ITU Radiocommunication Bureau (BR) | Records the satellite system in the Master International Frequency Register (MIFR) |

### 2.7.3 Common satellite frequency bands

| Band | Frequency range | Typical use | Key characteristics |
|------|----------------|-------------|-------------------|
| **UHF** | 400–450 MHz | CubeSat TT&C, AIS, ADS-B | Simple antennas, low data rate (1–9.6 kbps), crowded |
| **L-band** | 1.5–1.6 GHz | GNSS, mobile satellite service | Navigation, SAR beacons |
| **S-band** | 2.0–2.3 GHz | TT&C (uplink and downlink) | Standard for housekeeping; moderate antenna gain required |
| **C-band** | 3.7–4.2 / 5.9–6.4 GHz | Legacy GEO comms (DBS), SAR (RADARSAT) | Being repurposed for 5G in some countries |
| **X-band** | 8.025–8.4 GHz | EO payload data downlink | Higher data rates (10–150 Mbps); requires tracking antenna on ground |
| **Ka-band** | 26.5–40 GHz | High-throughput data downlink, inter-satellite links | Very high data rates (100+ Mbps); rain attenuation significant |

Whether a given allocation delivers enough performance is a link-budget question; the link budget equation and its margin criteria are developed in Chapter 11.

### 2.7.4 The licensing process (Canada)

The ISED spectrum licensing process for a satellite system follows the steps in Table 2.1. The timeline is long relative to a CubeSat development schedule, which is why spectrum work must start in Phase A. Figure 2.3 overlays the regulatory lead times on a 30-month Phase A–D schedule: the ITU coordination bar alone is as long as the whole development programme.

![Gantt chart of the regulatory steps for a Canadian CubeSat overlaid on a 30-month Phase A–D schedule.](../assets/figures/fig_licensing_timeline.png)

**Figure 2.3** — Indicative licensing timeline for a Canadian CubeSat (PDR at month 9, CDR at month 18, launch at month 30, as in Problem 4). The ISED pre-application and technical review and the ITU API filing follow Table 2.1; ITU coordination, at two to seven years, is the critical path and may run past launch (hatched); the RSSSA operating licence applies only to Earth-imaging missions; export permits (EIPA, and an ITAR TAA if US-origin parts are used) must be in hand before the spacecraft ships to the launch site.

**Table 2.1** — ISED/ITU spectrum licensing steps and indicative durations.

| Step | Activity | Duration | Documents |
|------|----------|----------|-----------|
| 1 | Pre-application consultation with ISED | 2–4 weeks | Preliminary technical description |
| 2 | Formal application submission | — | ISED application form, technical annex |
| 3 | ISED technical review | 3–6 months | Interference analysis, coordination requirements |
| 4 | ITU filing (Advance Publication Information — API) | — | ITU API filing (submitted by ISED on Canada's behalf) |
| 5 | ITU coordination with affected administrations | 2–7 years | Coordination agreements |
| 6 | ITU notification and recording in MIFR | — | MIFR entry |
| 7 | ISED licence issuance | — | Radio licence |

### 2.7.5 CubeSat-specific considerations

Many CubeSat operators use amateur radio frequencies (VHF/UHF) during development but must transition to commercial bands for operational missions, especially if there is any commercial data distribution.

| Approach | Licensing path | Limitations |
|----------|---------------|-------------|
| **Amateur radio (VHF/UHF)** | IARU coordination; national amateur licence | No commercial use; data must be freely available; limited power/bandwidth |
| **Commercial UHF** | ISED commercial licence; ITU coordination | Low data rate; crowded band; longer licensing timeline |
| **S-band TT&C** | ISED licence; SFCG coordination | Standard path; moderate timeline (6–12 months) |
| **X-band payload** | ISED licence; ITU coordination | Higher data rate; requires tracking ground station |

> **Industry practice.** Kepler Communications (Toronto) initially operated its first pathfinder satellites on Ku-band for store-and-forward IoT data relay. Obtaining Ku-band spectrum rights required coordination with incumbent GEO operators, a process that took over 2 years. The lesson: begin spectrum licensing as early as Phase A.

---

## 2.8 Export control

### 2.8.1 The export control landscape

Satellite technology is controlled goods in most countries due to dual-use (civil/military) applications. Canadian space companies and universities must navigate three overlapping regimes:

| Regime | Administered by | Scope | Key list |
|--------|----------------|-------|----------|
| **EIPA** (Canada) | Global Affairs Canada (GAC) | Canadian-origin goods and technology | Export Control List (ECL), Groups 1–7 |
| **ITAR** (USA) | US State Department (DDTC) | US-origin defence articles and services | US Munitions List (USML), Category XV (spacecraft) |
| **EAR** (USA) | US Commerce Department (BIS) | US-origin dual-use goods and technology | Commerce Control List (CCL), ECCN 9Axx |

### 2.8.2 Canadian export controls (EIPA)

The Export and Import Permits Act requires an export permit for goods on Canada's Export Control List (ECL). Space-relevant ECL groups:

| ECL group | Description | Examples |
|-----------|-------------|---------|
| Group 1 | Dual-use goods (Wassenaar Arrangement) | Radiation-hardened electronics, space-qualified components |
| Group 2 | Munitions (defence goods) | Military satellite systems, encrypted comms |
| Group 4 | Nuclear-related (NSG) | RTGs, nuclear propulsion components |
| Group 6 | Missile technology (MTCR) | Complete rocket systems, guidance systems, propulsion |
| Group 7 | Chemical/biological weapons | Not typically space-relevant |

### 2.8.3 US export controls (ITAR and EAR)

Any mission using US-origin components (which includes nearly all commercial space electronics) must comply with US export controls:

**ITAR (International Traffic in Arms Regulations):**

- USML Category XV covers spacecraft and related articles
- Requires a Technical Assistance Agreement (TAA) or Manufacturing License Agreement (MLA)
- Applies to US-origin defence articles regardless of where they are located
- Violation penalties: up to $1M per violation and 20 years imprisonment

**EAR (Export Administration Regulations):**

- Controls dual-use items (commercial space components, software, technology)
- Uses Export Control Classification Numbers (ECCNs)
- Requires a licence for export to most countries (except Canada for many items under bilateral agreements)
- The US–Canada Defence Production Sharing Agreement provides some exemptions

### 2.8.4 Practical implications for mission design

| Design decision | Export control implication |
|----------------|--------------------------|
| Using US-origin reaction wheels | EAR licence may be required; ITAR if military-grade |
| Collaborating with a non-Five Eyes university | TAA required for ITAR-controlled technical data |
| Launching on a non-US rocket | ITAR Technology Transfer Agreement for US components on foreign launcher |
| Open-sourcing satellite software | Must verify no controlled algorithms (e.g., encryption above EAR thresholds) |
| Hosting a foreign payload | May require export permit under EIPA and/or ITAR approval |
| Publishing detailed design in a paper | Technical data review required if ITAR-controlled components discussed |

> **Industry practice.** MDA's export of RADARSAT-2 ground segment technology to international partners required extensive EIPA permitting and ITAR compliance review (since US-origin components were embedded in the system). The process took 18+ months and required dedicated compliance staff. Even university CubeSat projects using US-origin COTS components must track their ECCN classifications.

---

## Summary

| Topic | Key takeaway |
|-------|-------------|
| CSA mandate | Promote peaceful use of space; niche excellence strategy (robotics, SAR, instruments) |
| Industry structure | 4-tier ecosystem; government seed funding enables commercial scale-up |
| RSSSA | Any remote sensing satellite operated from Canada requires a licence; includes shutter control |
| Spectrum licensing | Two-level process (ISED national + ITU international); start in Phase A; 2+ year timeline |
| Export control | Three overlapping regimes (EIPA, ITAR, EAR); nearly all missions encounter US controls |
| Key lesson | Regulatory compliance is not optional — it shapes design decisions from the earliest phases |

---

## Problems

1. **Engaging the ecosystem.** A university team is developing a 3U Earth-observation CubeSat with a multispectral imager for crop monitoring. Using §2.2, identify which industry tier(s) the team would engage for (a) the imager, (b) the attitude-control sensors, (c) launch brokerage and (d) data distribution. Which CSA or federal funding programmes in §2.2.3 might apply at each lifecycle phase, and which capabilities would most likely have to be sourced internationally?

2. **RSSSA applicability.** Decide, with reasons, whether an RSSSA licence is required for each of the following, and list the licence conditions from §2.6.3 that would most affect the design: (a) the 3U EO CubeSat above, operated from a Canadian university ground station; (b) UniSat-1, the 1U magnetometer demonstrator of Chapter 1 §1.7, which carries no camera; (c) a Canadian-built imaging satellite operated entirely from a partner's ground station in Germany; (d) a Canadian start-up that buys raw imagery from a foreign satellite and resells processed products.

3. **Band selection.** Using §2.7.3 and §2.7.5, choose a frequency band (or bands) for TT&C and for payload downlink for (a) UniSat-1, which must downlink about 1 MB per day, and (b) the 3U EO CubeSat, which must downlink at least 2 GB per day. For each choice, state the licensing path, the expected licensing timeline and one design consequence on the ground segment.

4. **Licensing on the critical path.** A CubeSat project plans PDR at month 9, CDR at month 18 and launch at month 30 after kick-off. Using the durations in Table 2.1, construct a timeline showing when the ISED pre-application, formal application, and ITU API filing must occur for the radio licence to be in hand before launch, assuming the shortest plausible ITU coordination period. Which regulatory step is on the critical path, and what happens to the schedule if coordination takes the longest duration in the table?

5. **Export control scenario.** The 3U EO CubeSat uses a US-origin reaction-wheel assembly and a US-origin GNSS receiver, will be launched on an Indian PSLV, and includes a visiting researcher from a non-Five Eyes country on the design team. Identify every export-control obligation from §2.8 that applies, name the regime and instrument (permit, TAA, ECCN classification, etc.) for each, and propose two design or programmatic changes that would reduce the compliance burden.

6. **Partnership leverage.** Using the leverage ratio of §2.4.2, estimate $L$ for Canada's Canadarm3 contribution to Artemis (committed to the Lunar Gateway in 2019; repurposed for lunar-surface operations after NASA paused Gateway in March 2026), stating your assumptions for $C_{\text{contribution}}$ and $V_{\text{access}}$. Discuss two limitations of the ratio as a decision metric, including what happens to $V_{\text{access}}$ when the partner restructures the programme, and propose one refinement.

7. **Comparing national models.** From the comparison in §2.3, identify two consequences for a Canadian mission design team of (a) the absence of domestic launch capability and (b) the small agency budget relative to NASA or ESA. How does ESA's *juste retour* model change the way a European team would approach supplier selection compared with a Canadian team?

8. **Regulation as a design driver.** For each of the three regulatory regimes in this chapter (RSSSA, spectrum, export control), write one requirement — in the "shall" form of Chapter 5 — that the 3U EO CubeSat must satisfy, and identify the lifecycle phase (Chapter 1 §1.4) by which the corresponding evidence must exist.

---

## References

1. Government of Canada, *Canadian Space Agency Act* (S.C. 1990, c. 13). [https://laws-lois.justice.gc.ca/eng/acts/c-11.2/](https://laws-lois.justice.gc.ca/eng/acts/c-11.2/)
2. Government of Canada, *Remote Sensing Space Systems Act* (S.C. 2005, c. 45). [https://laws-lois.justice.gc.ca/eng/acts/r-5.4/](https://laws-lois.justice.gc.ca/eng/acts/r-5.4/)
3. Government of Canada, *Radiocommunication Act* (R.S.C., 1985, c. R-2). [https://laws-lois.justice.gc.ca/eng/acts/r-2/](https://laws-lois.justice.gc.ca/eng/acts/r-2/)
4. Government of Canada, *Export and Import Permits Act* (R.S.C., 1985, c. E-19). [https://laws-lois.justice.gc.ca/eng/acts/e-19/](https://laws-lois.justice.gc.ca/eng/acts/e-19/)
5. ISED Canada, *Spectrum Management and Telecommunications*. [https://www.ic.gc.ca/eic/site/smt-gst.nsf/eng/home](https://www.ic.gc.ca/eic/site/smt-gst.nsf/eng/home)
6. ITU, *Radio Regulations*, Edition 2020. [https://www.itu.int/pub/R-REG-RR](https://www.itu.int/pub/R-REG-RR)
7. CSA, *Exploration, Imagination, Innovation: A New Space Strategy for Canada*, 2019. [https://www.asc-csa.gc.ca/eng/publications/space-strategy-for-canada.asp](https://www.asc-csa.gc.ca/eng/publications/space-strategy-for-canada.asp)
8. CSA, *State of the Canadian Space Sector Report*, 2022. [https://www.asc-csa.gc.ca/eng/publications/state.asp](https://www.asc-csa.gc.ca/eng/publications/state.asp)
9. US Department of State, *International Traffic in Arms Regulations* (22 CFR 120–130). [https://www.ecfr.gov/current/title-22/chapter-I/subchapter-M](https://www.ecfr.gov/current/title-22/chapter-I/subchapter-M)
10. US Department of Commerce, *Export Administration Regulations* (15 CFR 730–774). [https://www.ecfr.gov/current/title-15/subtitle-B/chapter-VII/subchapter-C](https://www.ecfr.gov/current/title-15/subtitle-B/chapter-VII/subchapter-C)
11. NASA, *Systems Engineering Handbook* (SP-2016-6105 Rev 2), 2016. [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/)
12. NASA, "NASA Unveils Initiatives to Achieve America's National Space Policy" (Gateway paused "in its current form"), news release, 24 March 2026. [https://www.nasa.gov/news-release/nasa-unveils-initiatives-to-achieve-americas-national-space-policy/](https://www.nasa.gov/news-release/nasa-unveils-initiatives-to-achieve-americas-national-space-policy/)
13. MDA Space, "MDA Space responds to Canadian Space Agency announcement on Canadarm3" (CSA repurposing of Canadarm3 for lunar-surface operations), 6 August 2026. [https://mda.space/article/mda-space-responds-to-canadian-space-agency-announcement-on-canadarm3](https://mda.space/article/mda-space-responds-to-canadian-space-agency-announcement-on-canadarm3)
