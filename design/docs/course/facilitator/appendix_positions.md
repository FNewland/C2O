# Appendix: Position-Specific Deep Dives

This appendix provides detailed guidance for each CDF engineering position,
including responsibilities, key parameters owned, decision authority,
common pitfalls, and references.

---

## Appendix A: Systems Engineer

**Responsibility:** Overall system architecture, budget management, cross-domain conflict resolution.

**Key Parameters Owned:** Mass margin, power margin, system-level cost, composite TRL, health score.

**Key Activities:**
- Maintain all engineering budgets (mass, power, cost, ?V, data, pointing)
- Apply ECSS margin policy by project phase (44% Phase A -> 13% Phase C/D)
- Resolve cross-domain conflicts (convene affected positions, facilitate trade)
- Prepare gate review evidence packages
- Own the requirements baseline and traceability matrix
- Conduct design reviews and track action items

**Decision Authority:** System-level trade-offs, margin allocation, requirement waivers.

**Common Pitfalls:**
- Allowing individual subsystems to consume their margin allocation (no system reserve)
- Not challenging HOW requirements that should be WHAT
- Accepting conflicts without resolution timelines
- Not tracking parametric estimate vs selected equipment delta

**References:** NASA SEH §2, §6; ECSS-E-ST-10C Rev.1 §5; SMAD4 Ch.3

---

## Appendix B: Mission Analyst

**Responsibility:** Orbit design, coverage analysis, ground station access, constellation architecture.

**Key Parameters Owned:** Altitude, inclination, orbit type, eclipse fraction, revisit time, contact time, LTAN.

**Key Activities:**
- Run orbit trade studies (altitude/inclination/lifetime/coverage/cost)
- Compute coverage and revisit for target latitude bands
- Analyse ground station access (elevation angle, contact duration, pass scheduling)
- Assess debris compliance (lifetime vs 25yr/5yr rules)
- For constellations: Walker delta design, phasing, coverage optimisation

**Key Formulae:**
- Period: T = 2pi?(a^3/mu)
- Eclipse fraction: f = (1/pi)arccos(?(1-(R_E/a)^2))
- SSO inclination: cos(i) = f(a, J2)
- Hohmann ?V: from vis-viva equation
- Coverage radius: from ground station elevation geometry

**References:** SMAD4 Ch.5-7; Vallado §2-9; ECSS-U-AS-10C Rev.2

---

## Appendix C: Payload Lead

**Responsibility:** Instrument performance, data generation, payload accommodation.

**Key Parameters Owned:** GSD (or equivalent MoP), data rate, pointing requirement, payload mass, power, duty cycle, FOV.

**Key Activities:**
- Size the payload from performance requirements (GSD -> aperture for optical; data rate -> antenna for comms; resolution -> antenna area for SAR)
- Define payload data volume and duty cycle
- Specify thermal environment needs (detector cooling, operational temperature)
- Coordinate with AOCS for pointing and stability requirements
- Coordinate with comms for downlink capacity matching data generation

**Key Formulae:**
- Optical: GSD = max(1.22lambdah/D, ph/f)
- Payload mass: M ~ 20D^1.5 + 2 (heritage CER)
- Data rate: R = N_pixels × N_bands × bit_depth × line_rate
- SAR: antenna_length >= 2 × resolution

**References:** SMAD4 Ch.9; ECSS-E-ST-10-06C; specific instrument handbooks

---

## Appendix D: Power Engineer

**Responsibility:** Solar array, battery, EPS architecture, power distribution, duty cycling.

**Key Parameters Owned:** SA area, SA power (BOL/EOL), battery capacity, bus voltage, power margin per mode.

**Key Activities:**
- Construct power budget per operational mode (safe/idle/imaging/downlink/eclipse)
- Size solar array from peak sunlight demand + battery recharge
- Size battery from eclipse energy / maximum DoD
- Define switched power line allocation per subsystem
- Assess SA degradation over mission lifetime
- Coordinate with thermal on SA/radiator area competition

**Key Formulae:**
- P_SA = P_peak_sun + (P_eclipse × t_ecl)/(t_sun × eta_charge)
- P_SA_BOL = P_SA_EOL / (1 - degradation)^years
- A_SA = P_BOL / (eta_cell × S × cos(theta) × eta_pack)
- C_bat = (P_ecl × t_ecl) / (DoD × eta_discharge)

**References:** SMAD4 Ch.11.4; ECSS-E-ST-20C; vendor datasheets (GomSpace NanoPower)

---

## Appendix E: AOCS Engineer

**Responsibility:** Attitude determination and control, pointing accuracy, momentum management.

**Key Parameters Owned:** Pointing accuracy, stability, slew rate, wheel momentum, actuator mass/power.

**Key Activities:**
- Select AOCS architecture (passive magnetic -> MTQ -> RW -> RW+ST) based on pointing requirement
- Construct pointing error budget (RSS of all sources)
- Size reaction wheels for momentum storage and torque
- Size magnetorquers for momentum dumping
- Define safe mode attitude (sun-pointing) for power survival
- Assess disturbance torques (gravity gradient, magnetic, SRP, aero drag)

**Key Formulae:**
- RSS pointing: theta = ?(? theta?^2)
- Gravity gradient torque: T = (3mu/2R^3) × (I_z - I_x) × sin(2theta)
- Magnetic torque: T = m × B (dipole moment × field)
- Wheel momentum: H = T × t_accumulation

**References:** SMAD4 Ch.11.1; ECSS-E-ST-60-10C; Wertz §11.1

---

## Appendix F: Thermal Engineer

**Responsibility:** Temperature control (hot/cold case), radiators, heaters, MLI.

**Key Parameters Owned:** Max/min predicted temperatures, radiator area, heater power, thermal margin.

**Key Activities:**
- Define hot case (max solar + internal dissipation) and cold case (eclipse, min power)
- Select thermal control approach (passive coatings -> MLI -> heaters -> heat pipes)
- Size radiators to reject waste heat in hot case
- Size heaters to maintain minimum temperature in cold case (eclipse)
- Verify ECSS thermal margins (±5°C operating, ±10°C acceptance, ±15°C qualification)
- Coordinate with power on heater power budget and with structure on radiator mounting

**Key Formulae:**
- Stefan-Boltzmann: Q = ?sigmaAT? (radiative heat transfer)
- Equilibrium: Q_absorbed + Q_internal = Q_radiated
- Solar absorptance/emittance ratio (?/?) determines equilibrium temperature

**References:** SMAD4 Ch.11.5; ECSS-E-ST-31C; Gilmore, Spacecraft Thermal Control Handbook

---

## Appendix G: Communications Engineer

**Responsibility:** Link budget, transponder/antenna selection, frequency licensing, ground station network.

**Key Parameters Owned:** Link margin, data rate, frequency band, EIRP, antenna gain, modulation/coding.

**Key Activities:**
- Construct complete link budget (EIRP, FSPL, G/T, C/N0, Eb/N0, margin)
- Select frequency band based on data rate need and licensing constraints
- Select transponder and antenna (RF chain compatibility: band, impedance, polarisation)
- Coordinate with AOCS on antenna pointing accuracy
- Define ground station requirements (antenna size, G/T, location, contact schedule)
- Manage frequency licensing process (IARU/ISED/ITU as appropriate)

**Key Formulae:**
- FSPL = 20log10(4pid/lambda) dB
- EIRP = P_TX + G_TX - L_TX dBW
- Link margin = Eb/N0_avail - Eb/N0_req - L_impl dB

**References:** SMAD4 Ch.13; ECSS-E-ST-50-05C; ITU Radio Regulations; CCSDS 131.0-B

---

## Appendix H: Propulsion Engineer

**Responsibility:** ?V budget, propulsion system selection, propellant management.

**Key Parameters Owned:** Total ?V, Isp, propellant mass, thrust level, total impulse.

**Key Activities:**
- Construct ?V budget (orbit insertion, maintenance, collision avoidance, deorbit)
- Select propulsion technology (cold gas, electric, chemical) based on ?V and power
- Size propellant mass using Tsiolkovsky equation
- Coordinate with structure on tank mounting and plume impingement
- Assess debris compliance (deorbit capability vs natural lifetime)

**Key Formulae:**
- Tsiolkovsky: ?V = Isp × g0 × ln(m_initial/m_final)
- Propellant mass: m_p = m_dry × (e^(?V/(Isp·g0)) - 1)
- Total impulse: I_total = m_p × Isp × g0

**References:** SMAD4 Ch.17; Sutton & Biblarz, Rocket Propulsion Elements; vendor data

---

## Appendix I: Structures Engineer

**Responsibility:** Primary structure, mechanisms, CDS compliance, launch loads, integration.

**Key Parameters Owned:** Structure mass, natural frequency, margin of safety, deployer compatibility.

**Key Activities:**
- Select CubeSat structure (form factor, material, vendor)
- Verify CDS compliance (dimensions, rails, switches, RBF, CG)
- Analyse launch loads (quasi-static, random vibration, shock)
- Compute structural margin of safety (MoS)
- Design deployment mechanisms (antenna, solar panels, payload)
- Plan integration sequence (component -> board -> stack -> structure -> deployer)

**Key Formulae:**
- MoS = (Allowable / (Design × FoS)) - 1
- Natural frequency: f = (1/2pi)?(k/m)

**References:** CDS Rev 14.1; SMAD4 Ch.11.3; ECSS-E-ST-32C Rev.1; NASA GEVS

---

## Appendix J: Cost Engineer

**Responsibility:** Cost estimation, WBS, learning curves, risk-adjusted cost.

**Key Parameters Owned:** Total cost (MEUR), per-WBS element cost, launch cost, operations cost.

**Key Activities:**
- Construct WBS-level cost estimate (parametric early, bottom-up later)
- Apply CubeSat-specific COTS pricing where applicable
- Estimate learning curve effects for constellations
- Perform Monte Carlo cost risk analysis (P50/P70/P80)
- Track cost against programmatic ceiling
- Identify cost drivers and propose de-scope options

**References:** SMAD4 Ch.20; Aerospace Corp SSCM; NASA CEH; ECSS-M-ST-60C

---

## Appendix K: Compliance / Regulatory Engineer

**Responsibility:** ECSS standard compliance, frequency licensing, export control, debris mitigation.

**Key Parameters Owned:** Standard applicability matrix, filing status, export classification, debris compliance score.

**Key Activities:**
- Determine applicable ECSS/NASA standards and prepare tailoring matrix
- Manage frequency licensing process (IARU/ISED/ITU filings)
- Assess export control classification for all components (ITAR/EAR/CGP)
- Verify debris compliance (25yr IADC, 5yr FCC, casualty risk)
- Prepare RSSSA filing if mission has remote sensing capability
- File COPUOS registration post-launch

**References:** ECSS-S-ST-00-02C (tailoring); CPC-2-6-02 (ISED); RSSSA; ITU RR Article 9

---

## Appendix L: Ground Segment Engineer

**Responsibility:** Ground station network, MCS, data processing pipeline, ops concept.

**Key Parameters Owned:** Contact time per day, ground station locations, processing latency, data throughput.

**Key Activities:**
- Select ground station network (own station, KSAT, SatNOGS, DSN)
- Define MCS architecture (COSMOS, OpenMCT, Yamcs)
- Design data processing pipeline (L0 -> L1 -> L2 -> archive -> distribution)
- Plan operations concept (staffing, automation level, anomaly response)
- Coordinate with comms engineer on frequency bands and antenna requirements

**References:** SMAD4 Ch.14-15; ECSS-E-ST-70C; CCSDS standards

---

## Appendix M: Software Engineer

**Responsibility:** Flight software architecture, FDIR, TC/TM definition, ground software.

**Key Parameters Owned:** FSW architecture, mode definitions, command dictionary, telemetry list.

**Key Activities:**
- Define FSW architecture (mode manager, ADCS control, TM/TC handler, FDIR)
- Implement FDIR (Fault Detection, Isolation, Recovery) rules
- Define telecommand dictionary (all commands with parameters)
- Define telemetry dictionary (all HK and science packets)
- Define autonomous operations (time-tagged commands, on-board scheduling)
- Develop ground control software and procedures

**References:** ECSS-E-ST-70-01C; ECSS-E-ST-70-41C (PUS); CCSDS 133.0-B (Space Packet Protocol)

---

## Appendix N: Mission Operations Engineer

**Responsibility:** Operations concept, ground procedures, LEOP planning, anomaly response, scheduling.

**Key Parameters Owned:** Pass schedule, contact time, command load timing, housekeeping budget, anomaly recovery time.

**Key Activities:**
- Define operations concept (number of operators, shifts, automation level)
- Plan LEOP sequence (first contact, deployment, commissioning timeline)
- Define ground station network requirements (contact minutes per orbit, latency)
- Write nominal operations procedures (imaging, downlink, orbit maintenance)
- Define anomaly response procedures (safe mode recovery, contingencies)
- Plan scheduling and resource allocation (data volume vs contact time)

**Decision Authority:** Operations approach, automation vs manual, pass scheduling priority.

**Common Pitfalls:**
- Underestimating LEOP complexity (first hours are most critical)
- Not planning for degraded operations (single ground station, partial hardware)
- Assuming 24/7 staffing when budget supports only office hours
- Not accounting for seasonal ground station visibility

**References:** ECSS-E-ST-70C; ECSS-M-ST-10C Annex B (Operations); NASA SEH Appendix T (Phase E)

---

## Appendix O: Project Manager

**Responsibility:** Schedule, budget, team coordination, review preparation, stakeholder management.

**Key Parameters Owned:** Project schedule, cost breakdown, FTE allocation, risk register, milestone status.

**Key Activities:**
- Maintain project schedule with milestones and dependencies
- Track cost against budget (EAC, ETC, cost-to-complete)
- Coordinate between positions (ensure interface agreements are met)
- Prepare review data packages (SRR, PDR, CDR, FRR)
- Manage risk register (convene risk review boards)
- Interface with customer/stakeholder on requirements changes

**Decision Authority:** Schedule priorities, resource allocation, risk acceptance (with engineering concurrence).

**Common Pitfalls:**
- Not protecting schedule margin (consumed by early phases)
- Accepting scope creep without schedule/cost impact assessment
- Not tracking earned value (work done vs time spent)
- Holding reviews before engineering products are mature

**References:** ECSS-M-ST-10C (Project Management); NPR 7120.5 (NASA PM Requirements); PMI PMBOK

---

## Appendix P: User Representative

**Responsibility:** End-user needs, data product requirements, service level agreements, utilisation planning.

**Key Parameters Owned:** Data product specifications, latency requirements, coverage needs, user interface requirements.

**Key Activities:**
- Define data product requirements (format, resolution, accuracy, timeliness)
- Specify user access methods (API, web portal, direct download)
- Define service level agreements (availability, response time, data freshness)
- Validate that system design meets stakeholder expectations
- Represent user community in trade study decisions
- Plan user training and documentation

**Decision Authority:** Data product format, delivery mechanism, user interface design.

**Common Pitfalls:**
- Not distinguishing between "nice to have" and actual requirements
- Specifying implementation details instead of user needs
- Not considering different user types (research, commercial, public)
- Assuming unlimited bandwidth for data delivery

**References:** NASA SEH §4.1 (Stakeholder Expectations); ECSS-E-ST-10C §5.2 (Requirements); ISO 9241 (Usability)
