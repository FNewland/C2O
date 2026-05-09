# Session 1.3: International Standards for Space Systems

**Duration:** 4 hours (Tuesday PM + Wednesday)
**Prerequisites:** Sessions 1.1--1.2
**References:**
- [ECSS, ECSS System -- Description, Implementation and General Requirements (ECSS-S-ST-00C), 2020](https://ecss.nl/standard/ecss-s-st-00c-space-standardization-policy-and-organisation/)
- [NASA, Systems Engineering Handbook (SP-2016-6105 Rev 2), 2016](https://www.nasa.gov/reference/systems-engineering-handbook/)
- [CDS, Interface Definition Document for Launch Vehicle Adapters, Rev 14, 2023](https://www.spacex.com/rideshare/)
- [IADC, Space Debris Mitigation Guidelines (IADC-02-01 Rev 3), 2021](https://www.iadc-home.org/documents_public/)
- [ISO, ISO 24113:2023 -- Space Debris Mitigation Requirements, 2023](https://www.iso.org/standard/82450.html)
- [UNOOSA, COPUOS Guidelines for the Long-term Sustainability of Outer Space Activities, 2019](https://www.unoosa.org/oosa/en/ourwork/topics/long-term-sustainability-of-outer-space-activities.html)
- [ESA, Space Debris Mitigation Compliance Verification Guidelines (ESSB-HB-U-002), 2023](https://technology.esa.int/upload/media/47ypgb5qwq.pdf)

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Describe the ECSS standard framework and its hierarchical structure (Management, Engineering, Product Assurance, Sustainability)
2. Compare ECSS and NASA standards and identify equivalences
3. Explain the CDS Rev 14 interface standard and its role in launch vehicle integration
4. Apply space debris mitigation guidelines (IADC, ISO 24113, FCC 5-year rule) to mission design
5. Describe the role of COPUOS and the Outer Space Treaty framework
6. Use SpaceCDF's compliance tracking features

---

## Part 1: The ECSS Framework (Tuesday PM -- 2 hours)

---

### 1. Why Standards Matter in Space Engineering (20 min)

#### 1.1 The Cost of Non-Compliance

Space missions operate in an environment where failures are catastrophic, repair is impossible, and the consequences of interference or debris affect all space users. Standards exist to:

1. **Ensure mission safety and reliability** -- by codifying lessons learned from decades of space operations
2. **Enable interoperability** -- by defining common interfaces, data formats, and protocols
3. **Reduce cost** -- by providing proven design approaches rather than re-inventing solutions
4. **Satisfy regulatory requirements** -- by demonstrating compliance with national and international obligations
5. **Facilitate technology transfer** -- by establishing a common engineering language

> **Industry Practice:** The loss of the Mars Climate Orbiter (1999) is the canonical example of what happens without rigorous interface standards. Lockheed Martin's ground software produced thruster force data in pound-force seconds, while NASA's navigation software expected Newton-seconds. The spacecraft entered the Martian atmosphere at 57 km altitude instead of the planned 226 km and was destroyed. Total loss: $327.6M. This failure directly led to NASA's strengthening of Process 12 (Interface Management) in NPR 7123.1D. The lesson: standards and interface control are not bureaucratic overhead -- they are mission-critical.

#### 1.2 The Major Standard Frameworks

Three major standard frameworks govern space activities globally:

| Framework | Scope | Typical Adopter | Document Count |
|-----------|-------|----------------|---------------|
| **ECSS** (European Cooperation for Space Standardization) | Full lifecycle, all disciplines | ESA, European industry, CSA (partial) | 144 standards + 56 handbooks |
| **NASA Technical Standards** | NASA programs and projects | NASA centres, US contractors | NPR/NPD/NASA-STD series |
| **ISO TC 20/SC 14** | Space systems and operations | International (reference standard) | ~40 standards |

These frameworks are not mutually exclusive. Many missions (including Canadian ones) adopt a tailored combination: ECSS for systems engineering and product assurance, NASA standards for specific technical domains, and ISO for debris mitigation.

---

### 2. ECSS Standard Hierarchy (40 min)

#### 2.1 Structure

The ECSS system organises standards into four branches, each with three levels:

<!-- SVG DIAGRAM: ECSS Standard Hierarchy -->

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450" style="max-width:800px; font-family: 'Segoe UI', Arial, sans-serif; background: #fafafa; border: 1px solid #ddd; border-radius: 8px;">
  <!-- Title -->
  <text x="400" y="28" text-anchor="middle" font-size="15" font-weight="bold" fill="#1a1a2e">ECSS Standard Hierarchy</text>

  <!-- Top level: ECSS-S (System) -->
  <rect x="300" y="45" width="200" height="40" rx="6" fill="#37474f" stroke="#263238" stroke-width="2"/>
  <text x="400" y="70" text-anchor="middle" font-size="12" fill="white" font-weight="bold">ECSS-S: System Level</text>

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

#### 2.2 The Four Branches

| Branch | Code | Scope | Example Standard |
|--------|------|-------|-----------------|
| **Management** | M | Project management, planning, reviews, configuration management, risk management | ECSS-M-ST-10C Rev.1 (Space Project Management) |
| **Engineering** | E | Technical disciplines: systems, structures, thermal, EPS, comms, AOCS, software, ground | ECSS-E-ST-10C (Systems Engineering General Requirements) |
| **Product Assurance** | Q | Quality, reliability, safety, EEE components, materials, contamination | ECSS-Q-ST-10C (Product Assurance Management) |
| **Sustainability** | U | Space debris mitigation, end-of-life disposal, space environment protection | ECSS-U-AS-10C Rev.2 (adoption of ISO 24113) |

#### 2.3 Document Types

| Type | Code | Meaning | Obligation |
|------|------|---------|-----------|
| **Standard** | ST | Contains "shall" requirements -- mandatory when invoked | Must comply or formally request a waiver |
| **Handbook** | HB | Contains guidance, best practices, worked examples | Advisory -- not mandatory but strongly recommended |
| **Technical Memorandum** | TM | Contains background information, state of the art | Informative only |

#### 2.4 Tailoring

A critical concept in ECSS (and all standard frameworks) is **tailoring** -- the process of selecting which standards and which requirements within those standards apply to a given project.

ECSS-S-ST-00C defines three tailoring levels:

| Tailoring Level | Description | Typical Application |
|----------------|-------------|-------------------|
| **Full application** | All requirements of the invoked standard apply | Large ESA missions (Sentinel, JUICE) |
| **Partial application** | Selected clauses apply; others are waived with rationale | Medium missions, CSA projects |
| **Not applicable** | Standard is not invoked for this project | CubeSat missions, technology demonstrators |

The tailoring rationale is documented in the **Product Assurance and Safety Plan (PASP)** and the **Systems Engineering Management Plan (SEMP)**.

> **Key Equation:** The cost of standards compliance scales non-linearly with mission class. A rough relationship observed in ESA studies:
>
> $C_{compliance} \approx k \cdot M_{SC}^{0.7} \cdot N_{standards}^{0.3}$
>
> Where $M_{SC}$ is the spacecraft dry mass (kg), $N_{standards}$ is the number of invoked standards, and $k$ is a constant dependent on the organisation's maturity. For a 10 kg CubeSat invoking 5 standards, compliance costs are roughly 5--10% of mission cost. For a 1000 kg satellite invoking 40 standards, compliance costs can reach 15--20%.

---

### 3. Key ECSS Engineering Standards (30 min)

#### 3.1 Systems Engineering (ECSS-E-ST-10C)

This is the master engineering standard, equivalent to NASA's NPR 7123.1D. It defines:
- System engineering processes and activities
- Requirements engineering (writing, verification, traceability)
- Functional analysis and decomposition
- Interface management
- Configuration management (technical aspects)

| ECSS-E-ST-10C Concept | NASA Equivalent | Key Difference |
|----------------------|----------------|----------------|
| System requirements specification | Technical requirements baseline | ECSS requires a formal Requirements Specification Document (RSD) |
| Functional analysis | Logical decomposition (Process 3) | Similar scope |
| Verification matrix | Requirements verification matrix | ECSS uses a formal DRD (Document Requirements Definition) |
| Design justification file | Design solution baseline | ECSS requires a DJF that traces every design decision |

#### 3.2 Key Subsystem Standards

| Standard | Discipline | Key Requirements | NASA Equivalent |
|----------|-----------|-----------------|----------------|
| ECSS-E-ST-20C | Electrical & Electronic | EPS design, grounding, EMC, harness | NASA-STD-4003A (EEE), NASA-HDBK-4001 |
| ECSS-E-ST-31C | Thermal Control | Thermal design, analysis, testing | NASA-STD-5001B (Structural Design) |
| ECSS-E-ST-32C | Structures | Structural design, factors of safety, testing | NASA-STD-5001B, GEVS (GSFC-STD-7000A) |
| ECSS-E-ST-33-01C | Mechanisms | Mechanism design, testing, lubrication | NASA-STD-5017 |
| ECSS-E-ST-35C | Propulsion | Propulsion system design, testing | -- |
| ECSS-E-ST-40C | Software | SW development, verification, FDIR | NASA-STD-8739.8 |
| ECSS-E-ST-50C | Communications | Comms system design, link budget, protocols | CCSDS standards |
| ECSS-E-ST-60C | Control | AOCS design, pointing, navigation | -- |
| ECSS-E-ST-70C | Ground Systems | Ground segment design, operations | CCSDS standards |

#### 3.3 Structural Design Requirements (Example)

To illustrate the depth of ECSS standards, consider the structural design requirements from ECSS-E-ST-32C:

| Requirement | Value | Rationale |
|-------------|-------|-----------|
| Factor of Safety (FoS) -- Yield | $\geq 1.25$ | Prevent permanent deformation under limit loads |
| Factor of Safety -- Ultimate | $\geq 1.5$ | Prevent structural failure under ultimate loads |
| Qualification loads | $1.25 \times$ limit loads | Demonstrate margin beyond expected environment |
| First natural frequency (axial) | $> 25$ Hz typical (launcher-dependent) | Avoid coupling with launcher modes |
| First natural frequency (lateral) | $> 10$ Hz typical (launcher-dependent) | Avoid coupling with launcher modes |

> **Key Equation:** The margin of safety (MoS) is defined as:
>
> $MoS = \frac{\sigma_{allowable}}{FoS \times \sigma_{applied}} - 1$
>
> A positive MoS ($MoS > 0$) indicates the structure meets the requirement. A MoS of 0.0 means the structure exactly meets the requirement with no margin to spare.
>
> Example: If the allowable stress is 280 MPa, the applied stress is 150 MPa, and the FoS is 1.5:
>
> $MoS = \frac{280}{1.5 \times 150} - 1 = \frac{280}{225} - 1 = 0.244$

---

### 4. NASA Standards Comparison (20 min)

#### 4.1 NASA Technical Standards Architecture

NASA's standards are organised differently from ECSS. Key document types:

| Type | Code | Example | Obligation |
|------|------|---------|-----------|
| **NASA Policy Directive** | NPD | NPD 8700.1 (Safety and Mission Assurance) | Mandatory for all NASA programs |
| **NASA Procedural Requirement** | NPR | NPR 7123.1D (SE Processes) | Mandatory; defines processes and requirements |
| **NASA Technical Standard** | NASA-STD | NASA-STD-5001B (Structural Design) | Mandatory when invoked |
| **NASA Handbook** | NASA-HDBK | NASA-HDBK-4001 (EEE Parts) | Advisory guidance |
| **Special Publication** | SP | SP-2016-6105 (SEH) | Reference text |

#### 4.2 Cross-Reference Table

| Domain | ECSS Standard | NASA Standard | ISO Standard |
|--------|--------------|--------------|-------------|
| Systems Engineering | ECSS-E-ST-10C | NPR 7123.1D, SP-2016-6105 | ISO 15288 |
| Project Management | ECSS-M-ST-10C | NPR 7120.5F | ISO 21500 |
| Configuration Management | ECSS-M-ST-40C | NPR 7120.5F Ch. 4 | ISO 10007 |
| Risk Management | ECSS-M-ST-80C | NPR 8000.4B | ISO 31000 |
| Structural Design | ECSS-E-ST-32C | NASA-STD-5001B | -- |
| Debris Mitigation | ECSS-U-AS-10C | NASA-STD-8719.14A | ISO 24113 |
| Cleanliness | ECSS-Q-ST-70-01C | NASA-SN-C-0005 | ISO 14644 |
| Software | ECSS-E-ST-40C | NASA-STD-8739.8 | ISO 12207 |

---

## Part 2: Launch Interfaces, Debris Mitigation & International Law (Wednesday -- 2 hours)

---

### 5. CDS Rev 14 -- Launch Vehicle Interface Standard (30 min)

#### 5.1 What is the CDS?

The **Cubesat Design Specification (CDS)**, maintained by the California Polytechnic State University (Cal Poly) and updated by the CubeSat community, defines the mechanical, electrical, and operational interfaces between CubeSats and their deployment systems (P-PODs, ISIPOD, etc.).

[Source: CDS Rev 14, 2022, available via Cal Poly CubeSat Program]

#### 5.2 Key CDS Requirements

| Parameter | CDS Rev 14 Requirement | Rationale |
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

#### 5.3 Form Factors

| Form Factor | Dimensions (mm) | Mass Limit | Typical Applications |
|------------|-----------------|------------|---------------------|
| 1U | 100 x 100 x 113.5 | 2.0 kg | Technology demonstrators, IoT nodes |
| 1.5U | 100 x 100 x 170.2 | 3.0 kg | Enhanced technology demonstrators |
| 2U | 100 x 100 x 227.0 | 4.0 kg | Simple instruments, store-and-forward |
| 3U | 100 x 100 x 340.5 | 6.0 kg | Standard EO/science missions |
| 6U | 100 x 226.3 x 340.5 | 12.0 kg | Advanced EO, communications |
| 12U | 226.3 x 226.3 x 340.5 | 24.0 kg | High-performance missions |
| 16U | 226.3 x 226.3 x 454.0 | 32.0 kg | Near-microsatellite capability |

#### 5.4 Rideshare Launch Interfaces

For non-CubeSat smallsats (microsatellites 10--200 kg), the interface standard depends on the launch provider:

| Launch Provider | Interface Standard | Adapter Type | Key Document |
|----------------|-------------------|-------------|-------------|
| SpaceX (Rideshare) | ESPA-class | 15" or 24" ESPA port | SpaceX Rideshare User's Guide |
| Rocket Lab (Electron) | Custom separation system | Rocket Lab-provided | Electron Payload User's Guide |
| Arianespace (Vega-C) | ASAP-S | Multi-payload adapter | Vega-C User Manual |
| ISRO (PSLV) | Custom adapter | ISRO-provided | PSLV User Manual |

> **Industry Practice:** Planet Labs' SuperDove constellation (150+ satellites) uses a standardised 3U-plus form factor that is CDS-compliant but extends the standard with a custom deployer arrangement for batch deployment. Each SuperDove satellite (mass ~5.8 kg) carries a multispectral imager with 8 bands and ~3m GSD. The standardisation of the bus design enabled a manufacturing rate of 2+ satellites per week -- only possible because the CDS provides a stable interface baseline.

---

### 6. Space Debris Mitigation (40 min)

#### 6.1 The Debris Problem

As of 2025, there are approximately:
- **36,500+** tracked objects larger than 10 cm in Earth orbit
- **1,000,000+** estimated objects 1--10 cm (untracked, lethal to spacecraft)
- **130,000,000+** estimated objects 1 mm -- 1 cm (can damage components)

The debris population is growing due to collisions (the Kessler Syndrome), anti-satellite tests (e.g., Chinese ASAT 2007: 3,500+ tracked fragments), and the rapid growth of mega-constellations.

[Source: ESA Space Debris Office, Annual Report 2024; NASA ODPO Orbital Debris Quarterly News]

#### 6.2 Debris Mitigation Guidelines Hierarchy

| Level | Document | Scope | Status |
|-------|----------|-------|--------|
| **International voluntary** | IADC Space Debris Mitigation Guidelines (Rev 3, 2021) | Global best practice | Advisory; adopted by COPUOS |
| **International standard** | ISO 24113:2023 | Requirements for debris mitigation | Standard; invoked by many agencies |
| **European standard** | ECSS-U-AS-10C Rev.2 | ECSS adoption notice for ISO 24113 | Mandatory for ESA missions |
| **US regulation** | FCC 47 CFR 25.114(d)(14) | Post-mission disposal for US-licensed satellites | Legally binding for FCC licensees |
| **NASA standard** | NASA-STD-8719.14A | NASA process for limiting orbital debris | Mandatory for NASA missions |
| **ESA requirement** | ESA/ADMIN/IPOL(2023)2 | Clean Space requirements | Mandatory for ESA missions (2023+) |

#### 6.3 Key Debris Mitigation Requirements

| Requirement | Source | Value | Notes |
|-------------|--------|-------|-------|
| **Post-mission disposal** | IADC, ISO 24113 | $\leq 25$ years | Voluntary guideline; being tightened |
| **Post-mission disposal** | FCC (2024+) | $\leq 5$ years | Legally binding for FCC-licensed sats |
| **Probability of successful disposal** | ISO 24113 | $\geq 0.9$ | Must demonstrate reliability of deorbit mechanism |
| **Casualty risk on re-entry** | NASA-STD-8719.14A | $\leq 1:10{,}000$ per event | Drives material selection and design-for-demise |
| **Collision avoidance probability** | IADC | $< 10^{-4}$ per year (cumulative) | Drives orbit selection and manoeuvre capability |
| **Passivation** | ISO 24113, ECSS-U-AS-10C | All stored energy sources depleted at EOL | Batteries, pressure vessels, wheels, RF |

#### 6.4 Post-Mission Disposal Options

| Method | Applicable Orbit | Mechanism | Time to Re-entry |
|--------|-----------------|-----------|------------------|
| **Atmospheric drag (natural)** | LEO < 600 km | Natural orbital decay | Months to years |
| **Atmospheric drag (augmented)** | LEO < 700 km | Drag sail, drag tether | Weeks to years |
| **Propulsive deorbit** | LEO | Thrusters lower perigee to ~200 km | Days |
| **Graveyard orbit** | GEO | Raise orbit ~300 km above GEO | Indefinite (not re-entry) |
| **Heliocentric disposal** | Beyond GEO | Escape Earth orbit | N/A |

> **Key Equation:** The orbital lifetime of a satellite in LEO due to atmospheric drag is approximately:
>
> $\tau \approx \frac{C_D \cdot A \cdot \rho \cdot a^2}{2m} \cdot \text{(complex integral)}$
>
> A simpler rule-of-thumb for circular orbits:
>
> $\tau_{years} \approx \frac{h - 200}{30} \cdot \frac{m / A}{50}$
>
> Where $h$ is altitude in km, $m$ is mass in kg, and $A$ is the cross-sectional area in m$^2$. This is very approximate; actual lifetime depends on solar activity (which modulates atmospheric density at high altitudes), drag coefficient, and orbit eccentricity. Use NASA's DAS (Debris Assessment Software) or ESA's DRAMA tool for accurate predictions.
>
> More precisely, the ballistic coefficient is:
>
> $B = \frac{m}{C_D \cdot A}$
>
> Lower $B$ (lighter, larger area) means faster re-entry. A 3U CubeSat ($m \approx 4$ kg, $A \approx 0.03$ m$^2$, $C_D \approx 2.2$) at 400 km has $B \approx 61$ kg/m$^2$ and will re-enter within ~1--3 years depending on solar cycle.

#### 6.5 Practical Implications for Mission Design

| Design Decision | Debris Mitigation Impact |
|----------------|--------------------------|
| Orbit altitude selection | Altitudes > 600 km require active deorbit; > 700 km strongly discouraged for non-manoeuvrable spacecraft |
| Propulsion system | Required for altitudes > 500--600 km to meet 25-year (or 5-year FCC) rule |
| Passivation design | Must design battery disconnect, pressure relief, wheel spin-down circuits |
| Material selection | Aluminium structures preferred for design-for-demise; titanium and carbon fibre survive re-entry |
| Collision avoidance | Manoeuvre capability or conjunction assessment service (e.g., 18th SDS, ESA SSA) needed |

> **Industry Practice:** OneWeb (648 satellites at 1200 km) carries propulsion on every satellite specifically for end-of-life deorbit, since natural decay from 1200 km would take centuries. Each satellite carries sufficient propellant for multiple collision avoidance manoeuvres plus a complete deorbit burn to lower perigee below 300 km. The deorbit operation takes approximately 3 months per satellite.

---

### 7. International Space Law and COPUOS (30 min)

#### 7.1 The UN Space Treaties

The legal framework for space activities is established by five UN treaties negotiated under the Committee on the Peaceful Uses of Outer Space (COPUOS):

| Treaty | Year | Key Provisions | Ratification |
|--------|------|----------------|-------------|
| **Outer Space Treaty (OST)** | 1967 | Space is free for exploration; no national appropriation; states responsible for national activities; liability for damage | 114 parties (incl. Canada) |
| **Rescue Agreement** | 1968 | Return astronauts and space objects | 99 parties |
| **Liability Convention** | 1972 | Launching state liable for damage on Earth (absolute) and in space (fault-based) | 98 parties |
| **Registration Convention** | 1976 | States must register space objects with UN | 72 parties |
| **Moon Agreement** | 1979 | Moon and celestial bodies are "common heritage of mankind" | 18 parties (NOT US, Russia, China) |

#### 7.2 Key Legal Principles for Mission Design

| Principle | Source | Implication |
|-----------|--------|------------|
| **State responsibility** | OST Art. VI | The Government of Canada is internationally responsible for all Canadian space activities, including private/university missions |
| **Authorisation and supervision** | OST Art. VI | Canada must authorise and continuously supervise all non-governmental space activities (this is why RSSSA exists) |
| **Liability** | Liability Convention | Canada (as launching state) is liable for damage caused by Canadian satellites; absolute liability on Earth, fault-based in space |
| **Registration** | Registration Convention | Canada must register all space objects with the UN; CSA maintains the Canadian registry |
| **Non-contamination** | OST Art. IX | Must avoid harmful contamination of space and celestial bodies (planetary protection) |
| **Due regard** | OST Art. IX | Must conduct activities with "due regard" for other states' interests (debris mitigation) |

#### 7.3 COPUOS Long-Term Sustainability Guidelines (2019)

In 2019, COPUOS adopted 21 guidelines for the long-term sustainability of outer space activities. These are voluntary but politically significant:

| Guideline Category | Count | Key Points |
|--------------------|----|------------|
| Policy and regulatory | 7 | Adopt national regulatory frameworks, register space objects, share SSA data |
| Safety of operations | 4 | Conjunction assessment, collision avoidance, re-entry risk assessment |
| International cooperation | 4 | Share debris mitigation best practices, coordinate spectrum use |
| Scientific and technical | 6 | Improve debris models, develop removal technology, research space weather effects |

[Source: A/74/20, Report of COPUOS, 2019, Annex II]

---

### 8. SpaceCDF Compliance Features (20 min)

SpaceCDF tracks compliance through the **Compliance Engineer** position:

| Feature | What It Tracks | Automation Level |
|---------|---------------|-----------------|
| **Standard applicability matrix** | Which ECSS/NASA/ISO standards apply to this mission | Semi-automated (suggests based on mission type) |
| **Debris mitigation compliance** | Post-mission lifetime, passivation plan, casualty risk | Automated (calculates from orbit and mass) |
| **RSSSA checklist** | Licence requirements for Canadian remote sensing missions | Manual (checklist with guidance) |
| **Spectrum filing status** | ISED/ITU filing progress | Manual (status tracking) |
| **Export control classification** | ECCN/USML classification of key components | Manual (per-component) |
| **CDS compliance** | Mechanical/electrical interface compliance with CDS Rev 14 | Semi-automated (checks mass, dimensions, CG) |

**Exercise:** *In SpaceCDF, navigate to the Compliance panel. Review the debris mitigation compliance status for your mission. What orbit altitude would be needed to comply with the FCC 5-year rule without propulsion? Use the tool's orbital lifetime calculator.*

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| ECSS framework | Four branches (M, E, Q, U); three document types (ST, HB, TM); tailoring is essential |
| NASA standards | Organised as NPD/NPR/NASA-STD/NASA-HDBK; broadly equivalent to ECSS |
| CDS Rev 14 | Defines CubeSat mechanical/electrical/operational interfaces; compliance is required for rideshare launch |
| Debris mitigation | IADC 25-year rule; FCC 5-year rule (2024+); passivation required; drives orbit and propulsion design |
| International law | OST establishes state responsibility; Canada liable for all Canadian space activities |
| COPUOS | 21 sustainability guidelines (2019); voluntary but increasingly influential |
| Compliance in SpaceCDF | Tracked through the Compliance Engineer position; automated where possible |

---

## References

1. [ECSS, ECSS-S-ST-00C -- Space Standardization, 2020](https://ecss.nl/standard/ecss-s-st-00c-space-standardization-policy-and-organisation/)
2. [ECSS, ECSS-E-ST-10C -- System Engineering General Requirements, 2009](https://ecss.nl/standard/ecss-e-st-10c-system-engineering-general-requirements/)
3. [ECSS, ECSS-E-ST-32C Rev.1 -- Structural General Requirements, 2008](https://ecss.nl/standard/ecss-e-st-32c-rev-1-structural-general-requirements/)
4. [ECSS, ECSS-U-AS-10C Rev.2 -- Adoption Notice of ISO 24113, 2023](https://ecss.nl/standard/ecss-u-as-10c-rev-2/)
5. [ISO, ISO 24113:2023 -- Space Systems: Space Debris Mitigation Requirements, 2023](https://www.iso.org/standard/82450.html)
6. [IADC, IADC-02-01 Rev 3 -- Space Debris Mitigation Guidelines, 2021](https://www.iadc-home.org/documents_public/)
7. [Cal Poly, CubeSat Design Specification (CDS) Rev 14, 2022](https://www.cubesat.org/cubesatinfo)
8. [NASA, Systems Engineering Handbook (SP-2016-6105 Rev 2), 2016](https://www.nasa.gov/reference/systems-engineering-handbook/)
9. [NASA, NASA-STD-8719.14A -- Process for Limiting Orbital Debris, 2019](https://standards.nasa.gov/standard/oce/nasa-std-871914)
10. [UNOOSA, A/74/20 -- Report of COPUOS, 2019](https://www.unoosa.org/oosa/en/ourwork/copuos/2019/index.html)
11. [UNOOSA, Outer Space Treaty, 1967](https://www.unoosa.org/oosa/en/ourwork/spacelaw/treaties/outerspacetreaty.html)
12. [FCC, 47 CFR 25.114 -- Satellite Applications](https://www.ecfr.gov/current/title-47/chapter-I/subchapter-B/part-25)
