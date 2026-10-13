# Chapter 3 — International Standards for Space Systems

> **Recommended background.** ECSS-S-ST-00C (the ECSS system description); NASA Systems Engineering Handbook §6.5; the CubeSat Design Specification Rev 14; IADC Space Debris Mitigation Guidelines. This chapter builds on the SE framework of Chapter 1 and the Canadian regulatory context of Chapter 2.

## Learning objectives

By the end of this chapter, you will be able to:

1. Describe the ECSS standard framework and its hierarchical structure (Management, Engineering, Product Assurance, Sustainability)
2. Compare ECSS and NASA standards and identify equivalences
3. Explain the CDS Rev 14 interface standard and its role in launch vehicle integration
4. Apply space debris mitigation guidelines (IADC, ISO 24113, FCC 5-year rule) to mission design
5. Describe the role of COPUOS and the Outer Space Treaty framework
6. Set up compliance tracking for a small spacecraft mission and identify which checks can be automated

---

## 3.1 Why standards matter in space engineering

### 3.1.1 The cost of non-compliance

Space missions operate in an environment where failures are catastrophic, repair is impossible, and the consequences of interference or debris affect all space users. Standards exist to:

1. **Ensure mission safety and reliability** — by codifying lessons learned from decades of space operations
2. **Enable interoperability** — by defining common interfaces, data formats, and protocols
3. **Reduce cost** — by providing proven design approaches rather than re-inventing solutions
4. **Satisfy regulatory requirements** — by demonstrating compliance with national and international obligations
5. **Facilitate technology transfer** — by establishing a common engineering language

> **Industry practice.** The loss of the Mars Climate Orbiter (1999) is the canonical example of what happens without rigorous interface standards. Lockheed Martin's ground software produced thruster force data in pound-force seconds, while NASA's navigation software expected newton-seconds. The spacecraft entered the Martian atmosphere at 57 km altitude instead of the planned 226 km and was destroyed. Total loss: $327.6M. This failure directly led to NASA's strengthening of Process 12 (Interface Management) in NPR 7123.1D. The lesson: standards and interface control are not bureaucratic overhead — they are mission-critical.

### 3.1.2 The major standard frameworks

Three major standard frameworks govern space activities globally:

| Framework | Scope | Typical adopter | Document count |
|-----------|-------|----------------|---------------|
| **ECSS** (European Cooperation for Space Standardization) | Full lifecycle, all disciplines | ESA, European industry, CSA (partial) | 144 standards + 56 handbooks |
| **NASA Technical Standards** | NASA programmes and projects | NASA centres, US contractors | NPR/NPD/NASA-STD series |
| **ISO TC 20/SC 14** | Space systems and operations | International (reference standard) | ~40 standards |

These frameworks are not mutually exclusive. Many missions (including Canadian ones) adopt a tailored combination: ECSS for systems engineering and product assurance, NASA standards for specific technical domains, and ISO for debris mitigation.

---

## 3.2 ECSS standard hierarchy

### 3.2.1 Structure

The ECSS system organises standards into four branches, each with three levels. Figure 3.1 shows the hierarchy and the principal standards in each branch.

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450" style="max-width:800px; font-family: sans-serif;">
  <!-- Title -->
  <text x="400" y="28" text-anchor="middle" font-size="15" font-weight="bold" fill="#1a1a2e">ECSS standard hierarchy</text>

  <!-- Top level: ECSS-S (System) -->
  <rect x="300" y="45" width="200" height="40" rx="6" fill="#37474f" stroke="#263238" stroke-width="2"/>
  <text x="400" y="70" text-anchor="middle" font-size="12" fill="white" font-weight="bold">ECSS-S: System level</text>

  <!-- Branch boxes -->
  <rect x="30" y="130" width="160" height="40" rx="6" fill="#1565c0" stroke="#0d47a1" stroke-width="2"/>
  <text x="110" y="155" text-anchor="middle" font-size="11" fill="white" font-weight="bold">M: Management</text>

  <rect x="220" y="130" width="160" height="40" rx="6" fill="#2e7d32" stroke="#1b5e20" stroke-width="2"/>
  <text x="300" y="155" text-anchor="middle" font-size="11" fill="white" font-weight="bold">E: Engineering</text>

  <rect x="410" y="130" width="160" height="40" rx="6" fill="#e65100" stroke="#bf360c" stroke-width="2"/>
  <text x="490" y="155" text-anchor="middle" font-size="11" fill="white" font-weight="bold">Q: Product Assurance</text>

  <rect x="600" y="130" width="160" height="40" rx="6" fill="#6a1b9a" stroke="#4a148c" stroke-width="2"/>
  <text x="680" y="155" text-anchor="middle" font-size="11" fill="white" font-weight="bold">U: Sustainability</text>

  <!-- Connecting lines from S to branches -->
  <line x1="350" y1="85" x2="110" y2="130" stroke="#555" stroke-width="1.5"/>
  <line x1="380" y1="85" x2="300" y2="130" stroke="#555" stroke-width="1.5"/>
  <line x1="420" y1="85" x2="490" y2="130" stroke="#555" stroke-width="1.5"/>
  <line x1="450" y1="85" x2="680" y2="130" stroke="#555" stroke-width="1.5"/>

  <!-- Level descriptions for M branch -->
  <rect x="10" y="195" width="180" height="30" rx="4" fill="#e3f2fd" stroke="#1565c0" stroke-width="1"/>
  <text x="100" y="215" text-anchor="middle" font-size="9" fill="#0d47a1">ST: Standard (SHALL)</text>

  <rect x="10" y="235" width="180" height="30" rx="4" fill="#e3f2fd" stroke="#1565c0" stroke-width="1"/>
  <text x="100" y="255" text-anchor="middle" font-size="9" fill="#0d47a1">HB: Handbook (guidance)</text>

  <rect x="10" y="275" width="180" height="30" rx="4" fill="#e3f2fd" stroke="#1565c0" stroke-width="1"/>
  <text x="100" y="295" text-anchor="middle" font-size="9" fill="#0d47a1">TM: Technical Memo</text>

  <!-- Key M standards -->
  <text x="20" y="325" font-size="9" fill="#333" font-weight="bold">Key M standards:</text>
  <text x="20" y="340" font-size="8" fill="#555">ECSS-M-ST-10C: Project Management</text>
  <text x="20" y="353" font-size="8" fill="#555">ECSS-M-ST-40C: Configuration Mgmt</text>
  <text x="20" y="366" font-size="8" fill="#555">ECSS-M-ST-80C: Risk Management</text>

  <!-- Level descriptions for E branch -->
  <rect x="205" y="195" width="190" height="30" rx="4" fill="#e8f5e9" stroke="#2e7d32" stroke-width="1"/>
  <text x="300" y="215" text-anchor="middle" font-size="9" fill="#1b5e20">ST: Standard (SHALL)</text>

  <rect x="205" y="235" width="190" height="30" rx="4" fill="#e8f5e9" stroke="#2e7d32" stroke-width="1"/>
  <text x="300" y="255" text-anchor="middle" font-size="9" fill="#1b5e20">HB: Handbook (guidance)</text>

  <!-- Key E standards -->
  <text x="210" y="290" font-size="9" fill="#333" font-weight="bold">Key E standards:</text>
  <text x="210" y="305" font-size="8" fill="#555">ECSS-E-ST-10C: SE General</text>
  <text x="210" y="318" font-size="8" fill="#555">ECSS-E-ST-20C: Electrical &amp; Electronic</text>
  <text x="210" y="331" font-size="8" fill="#555">ECSS-E-ST-31C: Thermal Control</text>
  <text x="210" y="344" font-size="8" fill="#555">ECSS-E-ST-32C: Structures</text>
  <text x="210" y="357" font-size="8" fill="#555">ECSS-E-ST-33-01C: Mechanisms</text>
  <text x="210" y="370" font-size="8" fill="#555">ECSS-E-ST-35C: Propulsion</text>
  <text x="210" y="383" font-size="8" fill="#555">ECSS-E-ST-40C: Software</text>
  <text x="210" y="396" font-size="8" fill="#555">ECSS-E-ST-50C: Communications</text>
  <text x="210" y="409" font-size="8" fill="#555">ECSS-E-ST-60C: Control</text>
  <text x="210" y="422" font-size="8" fill="#555">ECSS-E-ST-70C: Ground Systems</text>

  <!-- Key Q standards -->
  <text x="415" y="195" font-size="9" fill="#333" font-weight="bold">Key Q standards:</text>
  <text x="415" y="210" font-size="8" fill="#555">ECSS-Q-ST-10C: PA Management</text>
  <text x="415" y="223" font-size="8" fill="#555">ECSS-Q-ST-20C: QA</text>
  <text x="415" y="236" font-size="8" fill="#555">ECSS-Q-ST-30C: Dependability</text>
  <text x="415" y="249" font-size="8" fill="#555">ECSS-Q-ST-40C: Safety</text>
  <text x="415" y="262" font-size="8" fill="#555">ECSS-Q-ST-60C: EEE Components</text>
  <text x="415" y="275" font-size="8" fill="#555">ECSS-Q-ST-70C: Materials &amp; Processes</text>

  <!-- Key U standards -->
  <text x="605" y="195" font-size="9" fill="#333" font-weight="bold">Key U standards:</text>
  <text x="605" y="210" font-size="8" fill="#555">ECSS-U-AS-10C: Adoption Notice</text>
  <text x="605" y="223" font-size="8" fill="#555">for ISO 24113 (debris mitigation)</text>
  <text x="605" y="248" font-size="8" fill="#555">ECSS-U-AS-10C Rev.2:</text>
  <text x="605" y="261" font-size="8" fill="#555">Space sustainability requirements</text>

  <!-- Legend -->
  <rect x="500" y="380" width="280" height="55" rx="4" fill="#fff9c4" stroke="#f9a825" stroke-width="1"/>
  <text x="510" y="397" font-size="9" fill="#333" font-weight="bold">Naming convention:</text>
  <text x="510" y="412" font-size="8" fill="#555">ECSS-[Branch]-[Type]-[Number][Level]</text>
  <text x="510" y="425" font-size="8" fill="#555">Example: ECSS-E-ST-10C = Engineering-Standard-10-Level C</text>
</svg>

**Figure 3.1** — The ECSS standard hierarchy: the system-level ECSS-S documents, the four branches (M, E, Q, U), the three document types (ST, HB, TM) and the principal standards in each branch.

### 3.2.2 The four branches

| Branch | Code | Scope | Example standard |
|--------|------|-------|-----------------|
| **Management** | M | Project management, planning, reviews, configuration management, risk management | ECSS-M-ST-10C Rev.1 (Space Project Management) |
| **Engineering** | E | Technical disciplines: systems, structures, thermal, EPS, comms, AOCS, software, ground | ECSS-E-ST-10C (Systems Engineering General Requirements) |
| **Product Assurance** | Q | Quality, reliability, safety, EEE components, materials, contamination | ECSS-Q-ST-10C (Product Assurance Management) |
| **Sustainability** | U | Space debris mitigation, end-of-life disposal, space environment protection | ECSS-U-AS-10C Rev.2 (adoption of ISO 24113) |

### 3.2.3 Document types

| Type | Code | Meaning | Obligation |
|------|------|---------|-----------|
| **Standard** | ST | Contains "shall" requirements — mandatory when invoked | Must comply or formally request a waiver |
| **Handbook** | HB | Contains guidance, best practices, worked examples | Advisory — not mandatory but strongly recommended |
| **Technical Memorandum** | TM | Contains background information, state of the art | Informative only |

### 3.2.4 Tailoring

A critical concept in ECSS (and all standard frameworks) is **tailoring** — the process of selecting which standards and which requirements within those standards apply to a given project.

ECSS-S-ST-00C defines three tailoring levels:

| Tailoring level | Description | Typical application |
|----------------|-------------|-------------------|
| **Full application** | All requirements of the invoked standard apply | Large ESA missions (Sentinel, JUICE) |
| **Partial application** | Selected clauses apply; others are waived with rationale | Medium missions, CSA projects |
| **Not applicable** | Standard is not invoked for this project | CubeSat missions, technology demonstrators |

The tailoring rationale is documented in the **Product Assurance and Safety Plan (PASP)** and the **Systems Engineering Management Plan (SEMP)**.

> **Key equation.** The cost of standards compliance scales non-linearly with mission class. A rough relationship observed in ESA studies:
>
> $$C_{\text{compliance}} \approx k \cdot M_{SC}^{0.7} \cdot N_{\text{standards}}^{0.3}$$
>
> where $M_{SC}$ is the spacecraft dry mass (kg), $N_{\text{standards}}$ is the number of invoked standards, and $k$ is a constant dependent on the organisation's maturity. For a 10 kg CubeSat invoking 5 standards, compliance costs are roughly 5–10 % of mission cost. For a 1000 kg satellite invoking 40 standards, compliance costs can reach 15–20 %.

---

## 3.3 Key ECSS engineering standards

### 3.3.1 Systems engineering (ECSS-E-ST-10C)

This is the master engineering standard, equivalent to NASA's NPR 7123.1D. It defines:

- System engineering processes and activities
- Requirements engineering (writing, verification, traceability)
- Functional analysis and decomposition
- Interface management
- Configuration management (technical aspects)

| ECSS-E-ST-10C concept | NASA equivalent | Key difference |
|----------------------|----------------|----------------|
| System requirements specification | Technical requirements baseline | ECSS requires a formal Requirements Specification Document (RSD) |
| Functional analysis | Logical decomposition (Process 3) | Similar scope |
| Verification matrix | Requirements verification matrix | ECSS uses a formal DRD (Document Requirements Definition) |
| Design justification file | Design solution baseline | ECSS requires a DJF that traces every design decision |

### 3.3.2 Key subsystem standards

| Standard | Discipline | Key requirements | NASA equivalent |
|----------|-----------|-----------------|----------------|
| ECSS-E-ST-20C | Electrical and Electronic | EPS design, grounding, EMC, harness | NASA-STD-4003A (EEE), NASA-HDBK-4001 |
| ECSS-E-ST-31C | Thermal Control | Thermal design, analysis, testing | NASA-STD-5001B (Structural Design) |
| ECSS-E-ST-32C | Structures | Structural design, factors of safety, testing | NASA-STD-5001B, GEVS (GSFC-STD-7000A) |
| ECSS-E-ST-33-01C | Mechanisms | Mechanism design, testing, lubrication | NASA-STD-5017 |
| ECSS-E-ST-35C | Propulsion | Propulsion system design, testing | — |
| ECSS-E-ST-40C | Software | SW development, verification, FDIR | NASA-STD-8739.8 |
| ECSS-E-ST-50C | Communications | Comms system design, link budget, protocols | CCSDS standards |
| ECSS-E-ST-60C | Control | AOCS design, pointing, navigation | — |
| ECSS-E-ST-70C | Ground Systems | Ground segment design, operations | CCSDS standards |

### 3.3.3 Structural design requirements (example)

To illustrate the depth of ECSS standards, consider the structural design requirements from ECSS-E-ST-32C:

| Requirement | Value | Rationale |
|-------------|-------|-----------|
| Factor of Safety (FoS) — yield | $\geq 1.25$ | Prevent permanent deformation under limit loads |
| Factor of Safety — ultimate | $\geq 1.5$ | Prevent structural failure under ultimate loads |
| Qualification loads | $1.25 \times$ limit loads | Demonstrate margin beyond expected environment |
| First natural frequency (axial) | $> 25$ Hz typical (launcher-dependent) | Avoid coupling with launcher modes |
| First natural frequency (lateral) | $> 10$ Hz typical (launcher-dependent) | Avoid coupling with launcher modes |

> **Key equation.** The margin of safety (MoS) is defined as
>
> $$MoS = \frac{\sigma_{\text{allowable}}}{FoS \times \sigma_{\text{applied}}} - 1$$
>
> A positive MoS ($MoS > 0$) indicates the structure meets the requirement. A MoS of 0.0 means the structure exactly meets the requirement with no margin to spare.
>
> Example: If the allowable stress is 280 MPa, the applied stress is 150 MPa, and the FoS is 1.5:
>
> $$MoS = \frac{280}{1.5 \times 150} - 1 = \frac{280}{225} - 1 = 0.244$$
>
> The structural use of this margin, and its derivation, are developed in Chapter 12 §12.1.6 and Part V §V.13.

---

## 3.4 NASA standards comparison

### 3.4.1 NASA technical standards architecture

NASA's standards are organised differently from ECSS. Key document types:

| Type | Code | Example | Obligation |
|------|------|---------|-----------|
| **NASA Policy Directive** | NPD | NPD 8700.1 (Safety and Mission Assurance) | Mandatory for all NASA programmes |
| **NASA Procedural Requirement** | NPR | NPR 7123.1D (SE Processes) | Mandatory; defines processes and requirements |
| **NASA Technical Standard** | NASA-STD | NASA-STD-5001B (Structural Design) | Mandatory when invoked |
| **NASA Handbook** | NASA-HDBK | NASA-HDBK-4001 (EEE Parts) | Advisory guidance |
| **Special Publication** | SP | SP-2016-6105 (SEH) | Reference text |

### 3.4.2 Cross-reference table

| Domain | ECSS standard | NASA standard | ISO standard |
|--------|--------------|--------------|-------------|
| Systems Engineering | ECSS-E-ST-10C | NPR 7123.1D, SP-2016-6105 | ISO 15288 |
| Project Management | ECSS-M-ST-10C | NPR 7120.5F | ISO 21500 |
| Configuration Management | ECSS-M-ST-40C | NPR 7120.5F Ch. 4 | ISO 10007 |
| Risk Management | ECSS-M-ST-80C | NPR 8000.4B | ISO 31000 |
| Structural Design | ECSS-E-ST-32C | NASA-STD-5001B | — |
| Debris Mitigation | ECSS-U-AS-10C | NASA-STD-8719.14A | ISO 24113 |
| Cleanliness | ECSS-Q-ST-70-01C | NASA-SN-C-0005 | ISO 14644 |
| Software | ECSS-E-ST-40C | NASA-STD-8739.8 | ISO 12207 |

---

## 3.5 CDS Rev 14 — launch vehicle interface standard

### 3.5.1 What is the CDS?

The **CubeSat Design Specification (CDS)**, maintained by the California Polytechnic State University (Cal Poly) and updated by the CubeSat community, defines the mechanical, electrical, and operational interfaces between CubeSats and their deployment systems (P-PODs, ISIPOD, etc.).

[Source: CDS Rev 14, 2022, available via Cal Poly CubeSat Program]

### 3.5.2 Key CDS requirements

| Parameter | CDS Rev 14 requirement | Rationale |
|-----------|----------------------|-----------|
| **Unit dimensions** | $100 \times 100 \times 113.5$ mm per U | Standard deployer rail spacing |
| **Mass per U** | $\leq 2.0$ kg (with waiver up to 2.66 kg for some deployers) | Deployer spring mechanism limits |
| **Rail material** | Hard-anodised aluminium (7075 or 6061-T6) | Deployer contact surface compatibility |
| **Centre of gravity** | Within 2 cm of geometric centre | Deployment dynamics, tumble rate control |
| **Deployables** | Must be constrained during launch; no protrusion beyond CubeSat envelope | Protect adjacent payloads in deployer |
| **Separation springs** | Prohibited on CubeSat (deployer provides) | Standardised deployment mechanism |
| **RF silence** | No RF transmission until 30 minutes after deployment | Avoid interference with launch vehicle |
| **Deployment switches** | Minimum 1 per deployable; 2 for redundancy | Prevent premature deployment |
| **Battery charge state** | Fully charged (recommended); charging from deployer not available | No power interface with deployer |
| **Propulsion** | If present: must be inhibited by 3 independent inhibits; no toxic propellants | Safety of primary payload and deployer |

### 3.5.3 Form factors

| Form factor | Dimensions (mm) | Mass limit | Typical applications |
|------------|-----------------|------------|---------------------|
| 1U | 100 × 100 × 113.5 | 2.0 kg | Technology demonstrators, IoT nodes |
| 1.5U | 100 × 100 × 170.2 | 3.0 kg | Enhanced technology demonstrators |
| 2U | 100 × 100 × 227.0 | 4.0 kg | Simple instruments, store-and-forward |
| 3U | 100 × 100 × 340.5 | 6.0 kg | Standard EO/science missions |
| 6U | 100 × 226.3 × 340.5 | 12.0 kg | Advanced EO, communications |
| 12U | 226.3 × 226.3 × 340.5 | 24.0 kg | High-performance missions |
| 16U | 226.3 × 226.3 × 454.0 | 32.0 kg | Near-microsatellite capability |

### 3.5.4 Rideshare launch interfaces

For non-CubeSat smallsats (microsatellites 10–200 kg), the interface standard depends on the launch provider (representative examples, not endorsements):

| Launch provider | Interface standard | Adapter type | Key document |
|----------------|-------------------|-------------|-------------|
| SpaceX (Rideshare) | ESPA-class | 15" or 24" ESPA port | SpaceX Rideshare User's Guide |
| Rocket Lab (Electron) | Custom separation system | Rocket Lab-provided | Electron Payload User's Guide |
| Arianespace (Vega-C) | ASAP-S | Multi-payload adapter | Vega-C User Manual |
| ISRO (PSLV) | Custom adapter | ISRO-provided | PSLV User Manual |

> **Industry practice.** Planet Labs' SuperDove constellation (150+ satellites) uses a standardised 3U-plus form factor that is CDS-compliant but extends the standard with a custom deployer arrangement for batch deployment. Each SuperDove satellite (mass ~5.8 kg) carries a multispectral imager with 8 bands and ~3 m GSD. The standardisation of the bus design enabled a manufacturing rate of 2+ satellites per week — only possible because the CDS provides a stable interface baseline.

---

## 3.6 Space debris mitigation

### 3.6.1 The debris problem

As of 2025, there are approximately:

- **36,500+** tracked objects larger than 10 cm in Earth orbit
- **1,000,000+** estimated objects 1–10 cm (untracked, lethal to spacecraft)
- **130,000,000+** estimated objects 1 mm–1 cm (can damage components)

The debris population is growing due to collisions (the Kessler Syndrome), anti-satellite tests (e.g., Chinese ASAT 2007: 3,500+ tracked fragments), and the rapid growth of mega-constellations.

[Source: ESA Space Debris Office, Annual Report 2024; NASA ODPO Orbital Debris Quarterly News]

### 3.6.2 Debris mitigation guidelines hierarchy

| Level | Document | Scope | Status |
|-------|----------|-------|--------|
| **International voluntary** | IADC Space Debris Mitigation Guidelines (Rev 3, 2021) | Global best practice | Advisory; adopted by COPUOS |
| **International standard** | ISO 24113:2023 | Requirements for debris mitigation | Standard; invoked by many agencies |
| **European standard** | ECSS-U-AS-10C Rev.2 | ECSS adoption notice for ISO 24113 | Mandatory for ESA missions |
| **US regulation** | FCC 47 CFR 25.114(d)(14) | Post-mission disposal for US-licensed satellites | Legally binding for FCC licensees |
| **NASA standard** | NASA-STD-8719.14A | NASA process for limiting orbital debris | Mandatory for NASA missions |
| **ESA requirement** | ESA/ADMIN/IPOL(2023)2 | Clean Space requirements | Mandatory for ESA missions (2023+) |

### 3.6.3 Key debris mitigation requirements

| Requirement | Source | Value | Notes |
|-------------|--------|-------|-------|
| **Post-mission disposal** | IADC, ISO 24113 | $\leq 25$ years | Voluntary guideline; being tightened |
| **Post-mission disposal** | FCC (2024+) | $\leq 5$ years | Legally binding for FCC-licensed satellites |
| **Probability of successful disposal** | ISO 24113 | $\geq 0.9$ | Must demonstrate reliability of deorbit mechanism |
| **Casualty risk on re-entry** | NASA-STD-8719.14A | $\leq 1:10{,}000$ per event | Drives material selection and design-for-demise |
| **Collision avoidance probability** | IADC | $< 10^{-4}$ per year (cumulative) | Drives orbit selection and manoeuvre capability |
| **Passivation** | ISO 24113, ECSS-U-AS-10C | All stored energy sources depleted at EOL | Batteries, pressure vessels, wheels, RF |

### 3.6.4 Post-mission disposal options

| Method | Applicable orbit | Mechanism | Time to re-entry |
|--------|-----------------|-----------|------------------|
| **Atmospheric drag (natural)** | LEO < 600 km | Natural orbital decay | Months to years |
| **Atmospheric drag (augmented)** | LEO < 700 km | Drag sail, drag tether | Weeks to years |
| **Propulsive deorbit** | LEO | Thrusters lower perigee to ~200 km | Days |
| **Graveyard orbit** | GEO | Raise orbit ~300 km above GEO | Indefinite (not re-entry) |
| **Heliocentric disposal** | Beyond GEO | Escape Earth orbit | N/A |

The decisive parameter is orbital lifetime. Figure 3.2 shows how lifetime varies with altitude for representative ballistic coefficients, together with the IADC 25-year and FCC 5-year limits; the equations below give a first estimate, and Chapter 7 treats the atmospheric-drag environment in detail.

![Orbital lifetime versus altitude for representative ballistic coefficients, with the FCC 5-year and IADC 25-year limits.](../assets/figures/fig_orbital_lifetime.png)

**Figure 3.2** — Orbital lifetime versus initial circular altitude for representative ballistic coefficients. The horizontal lines mark the FCC 5-year and IADC 25-year post-mission disposal limits; the altitude at which a given spacecraft's curve crosses each line is the highest orbit it may occupy without active deorbit capability.

> **Key equation.** The orbital lifetime of a satellite in LEO due to atmospheric drag is approximately
>
> $$\tau \approx \frac{C_D \cdot A \cdot \rho \cdot a^2}{2m} \cdot \text{(complex integral)}$$
>
> A simpler rule of thumb for circular orbits:
>
> $$\tau_{\text{years}} \approx \frac{h - 200}{30} \cdot \frac{m / A}{50}$$
>
> where $h$ is altitude in km, $m$ is mass in kg, and $A$ is the cross-sectional area in m². This is very approximate; actual lifetime depends on solar activity (which modulates atmospheric density at high altitudes), drag coefficient, and orbit eccentricity. Use NASA's DAS (Debris Assessment Software) or ESA's DRAMA tool for accurate predictions.
>
> More precisely, the ballistic coefficient is
>
> $$B = \frac{m}{C_D \cdot A}$$
>
> Lower $B$ (lighter, larger area) means faster re-entry. A 3U CubeSat ($m \approx 4$ kg, $A \approx 0.03$ m², $C_D \approx 2.2$) at 400 km has $B \approx 61$ kg/m² and will re-enter within ~1–3 years depending on solar cycle.

### 3.6.5 Practical implications for mission design

| Design decision | Debris mitigation impact |
|----------------|--------------------------|
| Orbit altitude selection | Altitudes > 600 km require active deorbit; > 700 km strongly discouraged for non-manoeuvrable spacecraft |
| Propulsion system | Required for altitudes > 500–600 km to meet 25-year (or 5-year FCC) rule |
| Passivation design | Must design battery disconnect, pressure relief, wheel spin-down circuits |
| Material selection | Aluminium structures preferred for design-for-demise; titanium and carbon fibre survive re-entry |
| Collision avoidance | Manoeuvre capability or conjunction assessment service (e.g., 18th SDS, ESA SSA) needed |

> **Industry practice.** OneWeb (648 satellites at 1200 km) carries propulsion on every satellite specifically for end-of-life deorbit, since natural decay from 1200 km would take centuries. Each satellite carries sufficient propellant for multiple collision avoidance manoeuvres plus a complete deorbit burn to lower perigee below 300 km. The deorbit operation takes approximately 3 months per satellite.

---

## 3.7 International space law and COPUOS

### 3.7.1 The UN space treaties

The legal framework for space activities is established by five UN treaties negotiated under the Committee on the Peaceful Uses of Outer Space (COPUOS):

| Treaty | Year | Key provisions | Ratification |
|--------|------|----------------|-------------|
| **Outer Space Treaty (OST)** | 1967 | Space is free for exploration; no national appropriation; states responsible for national activities; liability for damage | 114 parties (incl. Canada) |
| **Rescue Agreement** | 1968 | Return astronauts and space objects | 99 parties |
| **Liability Convention** | 1972 | Launching state liable for damage on Earth (absolute) and in space (fault-based) | 98 parties |
| **Registration Convention** | 1976 | States must register space objects with UN | 72 parties |
| **Moon Agreement** | 1979 | Moon and celestial bodies are "common heritage of mankind" | 18 parties (NOT US, Russia, China) |

### 3.7.2 Key legal principles for mission design

| Principle | Source | Implication |
|-----------|--------|------------|
| **State responsibility** | OST Art. VI | The Government of Canada is internationally responsible for all Canadian space activities, including private/university missions |
| **Authorisation and supervision** | OST Art. VI | Canada must authorise and continuously supervise all non-governmental space activities (this is why RSSSA exists — Chapter 2 §2.6) |
| **Liability** | Liability Convention | Canada (as launching state) is liable for damage caused by Canadian satellites; absolute liability on Earth, fault-based in space |
| **Registration** | Registration Convention | Canada must register all space objects with the UN; CSA maintains the Canadian registry |
| **Non-contamination** | OST Art. IX | Must avoid harmful contamination of space and celestial bodies (planetary protection) |
| **Due regard** | OST Art. IX | Must conduct activities with "due regard" for other states' interests (debris mitigation) |

### 3.7.3 COPUOS Long-Term Sustainability Guidelines (2019)

In 2019, COPUOS adopted 21 guidelines for the long-term sustainability of outer space activities. These are voluntary but politically significant:

| Guideline category | Count | Key points |
|--------------------|----|------------|
| Policy and regulatory | 7 | Adopt national regulatory frameworks, register space objects, share SSA data |
| Safety of operations | 4 | Conjunction assessment, collision avoidance, re-entry risk assessment |
| International cooperation | 4 | Share debris mitigation best practices, coordinate spectrum use |
| Scientific and technical | 6 | Improve debris models, develop removal technology, research space weather effects |

[Source: A/74/20, Report of COPUOS, 2019, Annex II]

---

## 3.8 Compliance tracking in a concurrent-design study

In a concurrent-design team the **Compliance Engineer** position (Chapter 1, Table 1.4; Part IV) owns the standards, licensing and export-control status of the design. The position maintains a compliance register with, at minimum, the items in Table 3.1. Some of these checks can be computed directly from the shared parametric model — orbital lifetime from altitude, mass and area; CDS mass, dimensions and centre-of-gravity limits — and a concurrent-design tool can flag them automatically whenever a parameter changes. Others are inherently manual: licence filings, export classifications and the applicability of a standard are matters of judgement and paperwork that the register records but cannot decide.

**Table 3.1** — Items in a mission compliance register and the degree to which each can be automated.

| Item | What it tracks | Automation level |
|---------|---------------|-----------------|
| **Standard applicability matrix** | Which ECSS/NASA/ISO standards apply to this mission, and at what tailoring level | Semi-automated (suggested from mission type; confirmed by judgement) |
| **Debris mitigation compliance** | Post-mission lifetime, passivation plan, casualty risk | Automated (calculated from orbit and mass) |
| **RSSSA checklist** | Licence requirements for Canadian remote sensing missions | Manual (checklist with guidance) |
| **Spectrum filing status** | ISED/ITU filing progress | Manual (status tracking) |
| **Export control classification** | ECCN/USML classification of key components | Manual (per component) |
| **CDS compliance** | Mechanical/electrical interface compliance with CDS Rev 14 | Semi-automated (checks mass, dimensions, CG) |

---

## Summary

| Topic | Key takeaway |
|-------|-------------|
| ECSS framework | Four branches (M, E, Q, U); three document types (ST, HB, TM); tailoring is essential |
| NASA standards | Organised as NPD/NPR/NASA-STD/NASA-HDBK; broadly equivalent to ECSS |
| CDS Rev 14 | Defines CubeSat mechanical/electrical/operational interfaces; compliance is required for rideshare launch |
| Debris mitigation | IADC 25-year rule; FCC 5-year rule (2024+); passivation required; drives orbit and propulsion design |
| International law | OST establishes state responsibility; Canada liable for all Canadian space activities |
| COPUOS | 21 sustainability guidelines (2019); voluntary but increasingly influential |
| Compliance tracking | Owned by the Compliance Engineer position; automated where the check is numerical, manual where it is a filing or a judgement |

---

## Problems

1. **Interfaces and the Mars Climate Orbiter.** Identify which of the 17 common technical processes of Chapter 1 §1.3 failed in the Mars Climate Orbiter loss, and write the interface requirement (in the "shall" form of Chapter 5) that, had it been in the interface control document and verified, would have prevented the loss. Which verification method (ATIR(D)) would you assign to it?

2. **Tailoring a standards set.** For a 3U Earth-observation CubeSat built by a university team with a modest budget, select five ECSS standards from Figure 3.1 to invoke. For each, state the tailoring level (full, partial, not applicable), give a one-sentence rationale, and name the document (PASP or SEMP) in which the rationale would be recorded. Identify one standard you deliberately did *not* invoke and explain the risk you accept by omitting it.

3. **Compliance cost scaling.** Using the relationship in §3.2.4, compute the ratio of compliance cost between a 1000 kg satellite invoking 40 standards and a 10 kg CubeSat invoking 5 standards, assuming the same $k$. If mission cost scales roughly as $M_{SC}^{0.9}$, is the quoted rise in compliance cost from 5–10 % to 15–20 % of mission cost consistent with the equation? Comment on what the exponents imply about where compliance effort should be concentrated for small missions.

4. **Margin of safety.** A CubeSat rail is machined from aluminium 7075-T6 (yield allowable 503 MPa, ultimate allowable 572 MPa). Analysis gives an applied stress of 310 MPa at limit load. Compute the margin of safety against yield (FoS 1.25) and against ultimate (FoS 1.5) using §3.3.3. Which case governs? What applied stress would reduce the governing margin to zero, and what qualification load (in multiples of limit load) would the structure then have to survive?

5. **CDS compliance audit.** Returning to UniSat-1 (Chapter 1 §1.7): the design has a mass of 1.0 kg, a centre of gravity 1.5 cm from the geometric centre along the long axis, a deployable UHF tape antenna, and a transmitter that must remain silent after deployment. Check each row of §3.5.2 against the design and state whether it is compliant, non-compliant or needs a design feature added. Repeat for a 3U EO CubeSat of 4.2 kg with deployable solar panels and a cold-gas propulsion module.

6. **Orbital lifetime and the 5-year rule.** (a) Use the rule of thumb in §3.6.4 to estimate the orbital lifetime of a 3U CubeSat ($m = 4$ kg, $A = 0.03$ m²) at 400, 500 and 600 km, and of UniSat-1 ($m = 1$ kg, $A = 0.01$ m²) at 400 km. (b) Compare your 400 km result with the ballistic-coefficient statement in the same section ("~1–3 years") and with Figure 3.2. The estimates disagree; explain why a rule of thumb that ignores solar activity and atmospheric density can be wrong by a large factor, and state which source you would rely on at a design review (the physics-based calculation of Chapter 7 §7.3.3 gives ≈ 9 months at 400 km and ≈ 5 yr at 500 km for the 3U case). (c) Estimate, from Figure 3.2, the highest circular altitude at which the 3U CubeSat could operate without propulsion and still meet the FCC 5-year rule.

7. **Passivation.** List every stored-energy source on a 3U EO CubeSat that carries a lithium-ion battery, three reaction wheels, a cold-gas propulsion module and an S-band transmitter. For each, state the passivation action required by ISO 24113 at end of life and the design feature (circuit, valve, command) that enables it. Which of these actions must still work after the primary flight computer has failed?

8. **Launching state and liability.** A Canadian university CubeSat is launched on an Indian PSLV under a contract brokered by a Dutch company and, three years later, collides with a defunct Russian upper stage. Using §3.7, identify which states are "launching states" under the Liability Convention, whether absolute or fault-based liability applies, and which state must have registered the CubeSat. What does OST Art. VI imply about the university's obligations to the Government of Canada before launch?

9. **Building a compliance register.** For the 3U EO CubeSat, build a compliance register in the format of Table 3.1 with at least eight rows, covering standards applicability, debris mitigation, RSSSA, spectrum, export control and CDS. For each row, state the parameter(s) in the shared design model it depends on, whether the check can be automated, and the lifecycle phase (Chapter 1 §1.4) by which it must be closed.

---

## References

1. ECSS, *ECSS-S-ST-00C — Space Standardization: Policy and Organisation*, 2020. [https://ecss.nl/standard/ecss-s-st-00c-space-standardization-policy-and-organisation/](https://ecss.nl/standard/ecss-s-st-00c-space-standardization-policy-and-organisation/)
2. ECSS, *ECSS-E-ST-10C — System Engineering General Requirements*, 2009. [https://ecss.nl/standard/ecss-e-st-10c-system-engineering-general-requirements/](https://ecss.nl/standard/ecss-e-st-10c-system-engineering-general-requirements/)
3. ECSS, *ECSS-E-ST-32C Rev.1 — Structural General Requirements*, 2008. [https://ecss.nl/standard/ecss-e-st-32c-rev-1-structural-general-requirements/](https://ecss.nl/standard/ecss-e-st-32c-rev-1-structural-general-requirements/)
4. ECSS, *ECSS-U-AS-10C Rev.2 — Adoption Notice of ISO 24113*, 2023. [https://ecss.nl/standard/ecss-u-as-10c-rev-2/](https://ecss.nl/standard/ecss-u-as-10c-rev-2/)
5. ISO, *ISO 24113:2023 — Space Systems: Space Debris Mitigation Requirements*, 2023. [https://www.iso.org/standard/82450.html](https://www.iso.org/standard/82450.html)
6. IADC, *IADC-02-01 Rev 3 — Space Debris Mitigation Guidelines*, 2021. [https://www.iadc-home.org/documents_public/](https://www.iadc-home.org/documents_public/)
7. Cal Poly, *CubeSat Design Specification (CDS) Rev 14*, 2022. [https://www.cubesat.org/cubesatinfo](https://www.cubesat.org/cubesatinfo)
8. NASA, *Systems Engineering Handbook* (SP-2016-6105 Rev 2), 2016. [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/)
9. NASA, *NASA-STD-8719.14A — Process for Limiting Orbital Debris*, 2019. [https://standards.nasa.gov/standard/oce/nasa-std-871914](https://standards.nasa.gov/standard/oce/nasa-std-871914)
10. UNOOSA, *A/74/20 — Report of COPUOS*, 2019. [https://www.unoosa.org/oosa/en/ourwork/copuos/2019/index.html](https://www.unoosa.org/oosa/en/ourwork/copuos/2019/index.html)
11. UNOOSA, *Outer Space Treaty*, 1967. [https://www.unoosa.org/oosa/en/ourwork/spacelaw/treaties/outerspacetreaty.html](https://www.unoosa.org/oosa/en/ourwork/spacelaw/treaties/outerspacetreaty.html)
12. UNOOSA, *COPUOS Guidelines for the Long-term Sustainability of Outer Space Activities*, 2019. [https://www.unoosa.org/oosa/en/ourwork/topics/long-term-sustainability-of-outer-space-activities.html](https://www.unoosa.org/oosa/en/ourwork/topics/long-term-sustainability-of-outer-space-activities.html)
13. ESA, *Space Debris Mitigation Compliance Verification Guidelines* (ESSB-HB-U-002), 2023. [https://technology.esa.int/upload/media/47ypgb5qwq.pdf](https://technology.esa.int/upload/media/47ypgb5qwq.pdf)
14. FCC, *47 CFR 25.114 — Satellite Applications*. [https://www.ecfr.gov/current/title-47/chapter-I/subchapter-B/part-25](https://www.ecfr.gov/current/title-47/chapter-I/subchapter-B/part-25)
