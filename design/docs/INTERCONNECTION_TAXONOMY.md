# CDF Design Parameter Interconnection Taxonomy

## 220 interconnections across 27 categories

Used to build the SpaceCDF constraint propagation engine.

## 1. ORBIT <-> EVERYTHING

### 1.1 Orbit -> Payload Performance

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 1 | Altitude -> GSD | Orbit->Payload | Linear (proportional) | GSD = h * p / f; +10km altitude ~ +0.5m GSD for typical EO | Mission Analysis, Payload | -- |
| 2 | Altitude -> Diffraction limit | Orbit->Payload | Linear | GRD = 1.22 * h * lambda / D; sets min aperture | Mission Analysis, Payload | -- |
| 3 | Altitude -> Swath width | Orbit->Payload | Linear | Swath = 2*h*tan(FOV/2); wider at higher alt | Mission Analysis, Payload | -- |
| 4 | Altitude -> Revisit time | Orbit->Payload | Inverse (approx) | Lower alt = narrower swath = longer revisit; depends on constellation | Mission Analysis | -- |
| 5 | Inclination -> Coverage latitude | Orbit->Payload | Threshold/discrete | Max latitude covered = inclination; SSO ~98 deg for full-earth | Mission Analysis | -- |
| 6 | Altitude -> Signal-to-Noise (optical) | Orbit->Payload | Inverse-square | Irradiance at aperture ~ 1/h^2; higher alt = less signal | Payload | -- |
| 7 | Eccentricity -> Variable GSD | Orbit->Payload | Proportional | GSD varies between perigee/apogee by ratio (1+e)/(1-e) | Mission Analysis, Payload | -- |
| 8 | LTAN -> Illumination conditions | Orbit->Payload | Discrete/angular | Dawn-dusk vs noon orbit; affects shadowing, sun-glint | Mission Analysis, Payload | -- |

### 1.2 Orbit -> Power

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 9 | Altitude -> Eclipse fraction | Orbit->Power | Nonlinear (geometric) | f_ecl = (1/pi)*arcsin(R_E/(R_E+h)); ~35% at 400km LEO, ~0% at GEO | Mission Analysis, Power | ECSS-E-ST-20C Rev.2 |
| 10 | Beta angle -> Eclipse duration | Orbit->Power | Trigonometric | At beta > ~70 deg, no eclipse (full sun); varies with season | Mission Analysis, Power | -- |
| 11 | Altitude -> Solar flux (direct) | Orbit->Power | Negligible in LEO | Constant ~1361 W/m^2 (varies only with solar distance) | Power | ECSS-E-ST-10-04C Rev.1 |
| 12 | Eclipse duration -> Battery depth of discharge | Orbit->Power | Linear | Longer eclipse = deeper DoD; P_ecl * T_ecl = E_battery * DoD | Power | ECSS-E-ST-20-20C |
| 13 | Orbit period -> SA charge time | Orbit->Power | Linear | Sunlit time = Period * (1 - f_ecl); must charge battery fully | Power | -- |
| 14 | Orbit -> SA degradation rate | Orbit->Power | Proportional (radiation) | Higher radiation orbit = faster Pmax decline; ~2-3%/yr LEO, up to 10%/yr MEO | Power, Radiation | ECSS-E-ST-20-08C Rev.2 |

### 1.3 Orbit -> Thermal

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 15 | Altitude -> Earth IR flux | Orbit->Thermal | Inverse-square (approx) | ~240 W/m^2 at surface; decreases as (R_E/(R_E+h))^2 | Thermal | ECSS-E-ST-10-04C Rev.1 |
| 16 | Altitude -> Albedo flux | Orbit->Thermal | Inverse-square (approx) | ~0.3 * solar constant * view factor; diminishes with altitude | Thermal | ECSS-E-ST-10-04C Rev.1 |
| 17 | Beta angle -> Hot/cold case ratio | Orbit->Thermal | Angular | High beta = continuous sun on one face; low beta = symmetric heating | Thermal, Mission Analysis | ECSS-E-ST-31C |
| 18 | Eclipse -> Transient cold case | Orbit->Thermal | Step function | Eclipse entry = abrupt loss of solar input; ~35 min cold soak at 400km | Thermal | ECSS-E-ST-31C |
| 19 | LTAN -> Thermal cycling frequency | Orbit->Thermal | Discrete | Dawn-dusk orbit: minimal cycling; noon orbit: max hot/cold contrast | Thermal | -- |

### 1.4 Orbit -> Communications Link

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 20 | Altitude -> Max slant range | Orbit->Comms | Geometric | R_max = sqrt((R_E+h)^2 - R_E^2); ~2300 km at 400km alt, 5 deg elev | Comms | ECSS-E-ST-50C Rev.2 |
| 21 | Altitude -> Free space path loss | Orbit->Comms | Inverse-square (log) | FSPL = 20*log(d) + 20*log(f) + 32.44 dB; +6dB per doubling of range | Comms | -- |
| 22 | Altitude -> Contact duration | Orbit->Comms | Proportional | Higher alt = longer passes (~10 min at 400km, ~18 min at 800km, 5 deg elev) | Comms, Ground Segment | -- |
| 23 | Altitude -> Doppler shift | Orbit->Comms | Proportional to velocity | v ~ sqrt(mu/(R_E+h)); lower alt = higher velocity = more Doppler | Comms | ECSS-E-ST-50-02C |
| 24 | Inclination -> Ground station access | Orbit->Comms | Geometric/threshold | Station sees passes only if |lat_station| < inc + half-swath | Comms, Ground Segment | -- |
| 25 | Altitude -> Number of passes/day | Orbit->Comms | Inversely proportional | Lower alt = more revs/day (~15.5 at 400km vs ~14.2 at 800km) but shorter | Mission Analysis, Comms | -- |

### 1.5 Orbit -> Radiation

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 26 | Altitude -> TID (trapped belts) | Orbit->Radiation | Highly nonlinear | ~1 krad/yr at 400km; peaks ~10-100 krad/yr at 1000-2000km (inner belt); drops in slot, rises again at GEO | Radiation, EEE Components | ECSS-E-ST-10-04C Rev.1, ECSS-E-ST-10-12C |
| 27 | Inclination -> SAA exposure | Orbit->Radiation | Threshold | Inclinations >~30 deg cross SAA; polar orbits get max SAA exposure | Radiation | ECSS-Q-ST-60-15C Rev.1 |
| 28 | Altitude -> SEE rate | Orbit->Radiation | Nonlinear | Proton flux in SAA increases with altitude; GCR contribution increases outside magnetosphere | Radiation | ECSS-E-ST-10-12C |
| 29 | TID -> Shielding mass | Radiation->Structure | Proportional (log) | Each ~50% dose reduction requires ~2-4 mm Al additional shielding | Structure, Radiation | ECSS-Q-ST-60-15C Rev.1 |

### 1.6 Orbit -> Propulsion/Lifetime

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 30 | Altitude -> Atmospheric drag | Orbit->Propulsion | Exponential | Drag ~ rho(h) * v^2 * Cd * A; rho doubles every ~30-50km below 500km | Propulsion, Mission Analysis | ECSS-E-ST-10-04C Rev.1 |
| 31 | Altitude -> Station-keeping dV/yr | Orbit->Propulsion | Exponential | ~1-10 m/s/yr at 300-400km; <0.1 m/s/yr above 600km | Propulsion | -- |
| 32 | Altitude -> Natural decay lifetime | Orbit->Lifetime | Exponential | ~1yr at 350km; ~25yr at 600km; >500yr at 800km (A/m ~ 0.01) | Mission Analysis | ECSS-U-AS-10C Rev.2 (ISO 24113) |
| 33 | Altitude < 25-yr rule | Orbit->Propulsion | Threshold/compliance | If natural lifetime > 25 yr, deorbit propulsion required | Propulsion, Mission Analysis | ECSS-U-AS-10C Rev.2 |
| 34 | Eccentricity -> Perigee drag | Orbit->Propulsion | Nonlinear | Highly eccentric orbit: drag concentrated at perigee; circularizes naturally | Mission Analysis | -- |

### 1.7 Orbit -> Cost/Launch

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 35 | Inclination -> Launch site options | Orbit->Cost | Discrete | SSO requires high-lat launch (Vandenberg, Plesetsk, Vostochny); equatorial from Kourou/Cape | Mission Analysis, Cost | -- |
| 36 | Altitude -> Launch energy (C3) | Orbit->Cost | Linear (LEO) | dV to orbit ~ 9.3-9.7 km/s for LEO; higher alt = more dV = less mass margin | Mission Analysis | -- |
| 37 | Rideshare compatibility -> orbit selection | Cost->Orbit | Constraint | Low-cost rideshare limits orbit choice to what primary payload dictates | Cost, Mission Analysis | -- |

---

## 2. PAYLOAD <-> BUS

### 2.1 Payload -> AOCS

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 38 | Payload GSD requirement -> Pointing accuracy | Payload->AOCS | Proportional | Pointing error < 0.5*IFOV typically; 1m GSD at 500km needs ~0.2 mrad pointing | Payload, AOCS | ECSS-E-ST-60-30C |
| 39 | Pointing accuracy -> Sensor selection | AOCS internal | Threshold/discrete | >5 deg: sun sensors; 0.1-1 deg: magnetometer+gyro; <0.01 deg: star tracker | AOCS | ECSS-E-ST-60-20C Rev.2 |
| 40 | Pointing accuracy -> Actuator selection | AOCS internal | Threshold/discrete | >1 deg: MTQ only; 0.01-1 deg: RW+MTQ; <0.001 deg: RW+fine steering mirror | AOCS | ECSS-E-ST-60-30C |
| 41 | Payload agility requirement -> RW torque | Payload->AOCS | Linear | Slew rate = T_rw / I_sc; faster slew needs larger/more wheels | AOCS | -- |
| 42 | Payload stability requirement -> Jitter budget | Payload->AOCS | Proportional | Sub-pixel stability needs micro-vibration isolation; RW imbalance is primary source | AOCS, Structure, Payload | ECSS-E-ST-60-10C |

### 2.2 Payload -> Data/Comms

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 43 | Payload data rate -> On-board storage | Payload->Data | Linear | Storage = DataRate * MaxTime_between_contacts; e.g., 100 Mbps * 90 min = 67 GB | Data Handling, Comms | -- |
| 44 | Payload data rate -> Downlink requirement | Payload->Comms | Linear | Must downlink all data within available contact time per orbit | Comms | ECSS-E-ST-50C Rev.2 |
| 45 | Data volume -> Compression requirement | Payload->Data | Threshold | If raw data > downlink capacity, compression mandatory (2:1 to 10:1 typical) | Data Handling | -- |
| 46 | Number of spectral bands -> Data rate | Payload internal | Linear | More bands = proportional data increase | Payload, Data Handling | -- |

### 2.3 Payload -> Structure

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 47 | Payload mass -> Structure mass | Payload->Structure | Proportional | Structure ~ 15-25% of total mass; payload drives total mass | Structure | ECSS-E-ST-32C Rev.1 |
| 48 | Payload volume -> Form factor | Payload->Structure | Discrete/constraint | Large payloads may force larger bus size (3U->6U->12U for CubeSats) | Structure, Systems | -- |
| 49 | Payload optical aperture -> Baffle length | Payload->Structure | Proportional | Baffle ~2-4x aperture diameter; stray-light rejection drives length | Structure, Payload | -- |
| 50 | Payload FOV -> Mounting orientation constraint | Payload->Structure | Geometric | Nadir-pointing payload constrains which face is Earth-facing | Structure, AOCS | -- |

### 2.4 Payload -> Power

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 51 | Payload peak power -> EPS sizing | Payload->Power | Linear (with margin) | Payload typically 30-50% of total power; EPS sized for peak + 20% margin | Power | ECSS-E-ST-20-20C |
| 52 | Payload duty cycle -> Average power demand | Payload->Power | Linear | Avg_power = Peak * DutyCycle; lower duty = smaller SA needed | Power | -- |
| 53 | Payload thermal dissipation -> Heater savings | Payload->Thermal | Coupling | Active payload generates heat that reduces heater need (or adds cooling need) | Thermal, Power | -- |

### 2.5 Payload -> Thermal

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 54 | Payload operating temp range -> TCS complexity | Payload->Thermal | Threshold | Narrow range (e.g., IR detector at 80K) -> active cooling; wide range -> passive | Thermal | ECSS-E-ST-31C |
| 55 | Payload dissipation -> Radiator sizing | Payload->Thermal | Linear | A_rad = Q_diss / (epsilon * sigma * (T_rad^4 - T_sink^4)) | Thermal | -- |
| 56 | Cooled detector -> Cryocooler power | Payload->Power/Thermal | Step function | Cryocooler adds 10-80W depending on cold-tip temp; major power/mass/vibration hit | Power, Thermal, AOCS | -- |

### 2.6 Bus -> Payload (reverse constraints)

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 57 | Available power -> Payload duty cycle limit | Power->Payload | Inverse constraint | If SA/battery insufficient, payload must reduce duty cycle | Power, Payload | -- |
| 58 | AOCS capability -> Payload pointing limit | AOCS->Payload | Ceiling constraint | Bus pointing worse than payload need = degraded GSD or missed imagery | AOCS, Payload | -- |
| 59 | Downlink capacity -> Payload data collection limit | Comms->Payload | Inverse constraint | If downlink < generation rate, must reduce acquisition time or increase compression | Comms, Payload | -- |
| 60 | Structure mass limit -> Payload mass allocation | Structure->Payload | Ceiling constraint | Form factor imposes total mass ceiling; payload gets remainder after bus | Structure, Payload, Systems | -- |
| 61 | EMC environment -> Payload sensitivity limit | EPS/Comms->Payload | Threshold | Conducted/radiated emissions from bus may blind sensitive instruments | EMC, Payload | ECSS-E-ST-20-07C Rev.2 |

---

## 3. POWER CASCADES

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 62 | SA area -> SA mass | Power internal | Linear | ~0.8-2.5 kg/m^2 (body-mounted ~0.8; deployable with mechanism ~2.5) | Power, Structure | ECSS-E-ST-20-08C Rev.2 |
| 63 | SA area -> Drag area (LEO) | Power->Propulsion | Linear | Deployable panels increase cross-section; drag ~ Cd*A*rho*v^2/2 | Power, Propulsion | -- |
| 64 | SA area vs Radiator area | Power<->Thermal | Competing | Both need spacecraft exterior faces; allocation is zero-sum on small SC | Power, Thermal, Systems | -- |
| 65 | SA type (body vs deployable) -> Mechanism mass | Power->Mechanisms | Discrete step | Deployable adds ~0.3-1 kg for hinges + hold-down + actuator per wing | Power, Mechanisms | ECSS-E-ST-33-01C Rev.2 |
| 66 | SA deployment -> Reliability risk | Power->Dependability | Discrete | Single-point failure if deployment fails; may need redundant actuator | Mechanisms, PA | ECSS-Q-ST-30C Rev.1 |
| 67 | Battery capacity -> Battery mass | Power internal | Linear | Li-ion: ~150-250 Wh/kg; capacity = P_ecl * T_ecl / DoD / eta | Power | -- |
| 68 | Eclipse duration -> Battery capacity need | Orbit->Power | Linear | Direct: E_battery = P_load * T_eclipse / (DoD * eta_discharge) | Power, Mission Analysis | -- |
| 69 | Battery DoD -> Cycle life | Power internal | Inverse/exponential | 20% DoD: >50,000 cycles; 80% DoD: ~500 cycles | Power | -- |
| 70 | EPS conversion efficiency -> Thermal dissipation | Power->Thermal | Complementary | Heat = P_total * (1 - eta_EPS); typical eta 85-93%; 7-15% becomes heat | Power, Thermal | -- |
| 71 | Power margin policy -> Duty cycle limit | Power->Operations | Constraint | Phase A: 30% margin; Phase C: 10% margin (ECSS); constrains operations | Power, Systems | ECSS-E-ST-20-20C |
| 72 | Duty cycle -> Data generation rate | Power->Data | Linear | More payload ON time = more data; data budget must be consistent with power budget | Power, Data Handling | -- |
| 73 | Bus voltage selection -> Harness mass | Power->Structure | Nonlinear | Higher voltage = lower current = thinner cables = less mass (P=IV) | Power, Harness | ECSS-E-ST-20C Rev.2 |
| 74 | Peak power demand -> PCDU sizing | Power internal | Linear/discrete | PCDU must handle max simultaneous loads; drives mass and cost of power electronics | Power | ECSS-E-ST-20-20C |
| 75 | SA degradation (EOL) -> Oversizing at BOL | Power internal | Factor | SA sized for EOL power; BOL excess power must be dissipated or shunted | Power, Thermal | -- |

---

## 4. AOCS CASCADES

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 76 | Pointing requirement -> Sensor grade | AOCS internal | Threshold/discrete | <10 arcsec: star tracker (~0.3-0.5 kg, 1-2W); <1 deg: magnetometer (~50g, 0.2W) | AOCS | ECSS-E-ST-60-20C Rev.2 |
| 77 | Star tracker -> Exclusion angle constraint | AOCS->Structure | Geometric | Must avoid Sun/Earth/Moon in FOV (~20-45 deg exclusion); constrains mounting | AOCS, Structure | -- |
| 78 | Actuator type -> Power demand | AOCS->Power | Discrete/linear | MTQ: 0.1-1W; RW: 1-5W (standby), 10-40W (slew); CMG: 20-100W | AOCS, Power | -- |
| 79 | RW -> Micro-vibration -> Payload jitter | AOCS->Payload | Proportional | Imbalance forces at multiples of wheel speed; isolation needed for <1 arcsec stability | AOCS, Payload, Structure | ECSS-E-ST-60-10C |
| 80 | Momentum storage capacity -> Saturation time | AOCS internal | Linear | h_max / T_disturbance = time to saturation; lower orbit = faster saturation (aero torque) | AOCS | ECSS-E-ST-60-30C |
| 81 | Desaturation -> MTQ power demand | AOCS->Power | Periodic | Desaturation every 1-3 orbits typically; MTQ burst ~0.5-2W for 5-15 min | AOCS, Power | -- |
| 82 | Desaturation -> Orbit-dependent (B-field) | AOCS->Mission Analysis | Proportional | MTQ torque = m x B; B-field weaker at higher altitude and equator | AOCS, Mission Analysis | -- |
| 83 | Safe mode architecture -> Min power requirement | AOCS->Power | Constraint | Safe mode = sun-pointing (min attitude knowledge); must run on battery alone | AOCS, Power | -- |
| 84 | Number of RWs -> Redundancy/mass | AOCS->Structure | Discrete | 3 wheels min (no redundancy); 4 wheels (1 redundant); each ~0.2-1.5 kg | AOCS, Structure, PA | -- |
| 85 | SC inertia -> RW sizing | Structure->AOCS | Linear | Torque = I * alpha; larger SC needs larger wheels for same slew rate | Structure, AOCS | -- |
| 86 | CG offset -> Disturbance torques | Structure->AOCS | Linear | Aero torque = F_drag * d_CG_offset; gravity gradient ~ 3*n^2*(Iz-Ix)*sin(2theta)/2 | Structure, AOCS | -- |
| 87 | Deployable appendages -> Flexible mode coupling | Structure->AOCS | Resonance | SA flexible modes can couple with AOCS bandwidth; must separate by factor >3 | Structure, AOCS | ECSS-E-HB-60A |

---

## 5. COMMUNICATIONS CASCADES

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 88 | Data rate -> Required bandwidth | Comms internal | Proportional | BW ~ DataRate / SpectralEfficiency; QPSK ~2 bit/s/Hz; higher order = more efficient | Comms | ECSS-E-ST-50-05C Rev.2 |
| 89 | Bandwidth -> Frequency band selection | Comms internal | Discrete/regulatory | UHF: 1-5 kbps; S-band: 1-10 Mbps; X-band: 10-800 Mbps; Ka-band: 100 Mbps-2 Gbps | Comms | ECSS-E-ST-50-05C Rev.2 |
| 90 | Frequency -> Antenna size (for given gain) | Comms internal | Inverse | D = lambda / (pi * theta_3dB); higher freq = smaller dish for same gain | Comms | -- |
| 91 | Antenna size -> Pointing requirement | Comms->AOCS | Inverse (gain-beamwidth) | Beamwidth ~ 70*lambda/D; 0.3m X-band dish has ~7 deg beam; needs 1-2 deg pointing | Comms, AOCS | -- |
| 92 | High-gain antenna -> Pointing mechanism mass | Comms->Mechanisms | Discrete step | If antenna beam < attitude knowledge, need antenna pointing mechanism (2-axis gimbal) | Comms, Mechanisms | ECSS-E-ST-33-01C Rev.2 |
| 93 | TX power -> PA efficiency -> Heat dissipation | Comms->Thermal | Complementary | PA eta ~ 10-40%; 10W RF output with 25% eta = 30W heat to dissipate | Comms, Thermal | -- |
| 94 | TX power -> EPS demand | Comms->Power | Linear (with eta) | P_DC = P_RF / eta_PA; largest instantaneous power consumer on many small SC | Comms, Power | -- |
| 95 | Link margin -> Ground station G/T requirement | Comms<->Ground | Trade-off | Higher ground G/T = lower space TX power needed; ground antenna cost trade | Comms, Ground Segment | -- |
| 96 | Modulation + coding -> Eb/N0 requirement | Comms internal | Discrete | QPSK+LDPC 1/2: ~1 dB Eb/N0; uncoded BPSK: ~10 dB; 9 dB difference in link budget | Comms | ECSS-E-AS-50-21C Rev.2 |
| 97 | Frequency band -> Licensing + cost | Comms->Cost | Discrete/regulatory | UHF amateur: free but low rate; Ka-band: expensive license but high throughput | Comms, Cost | ITU Radio Regulations |
| 98 | Frequency -> Rain attenuation | Comms->Ground | Nonlinear | Ka-band: 3-10 dB fade in heavy rain; S-band: <0.5 dB; drives availability vs margin | Comms, Ground Segment | -- |
| 99 | Data throughput -> Contact strategy | Comms->Ops | Constraint | If single GS insufficient, need network (e.g., KSAT, AWS GS) -> cost | Comms, Ground Segment, Cost | -- |
| 100 | Comms EMI -> Payload interference | Comms->Payload | Threshold | TX harmonics/spurious can interfere with sensitive receivers/detectors | Comms, EMC, Payload | ECSS-E-ST-20-07C Rev.2 |

---

## 6. THERMAL CASCADES

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 101 | Total internal dissipation -> Radiator area | All->Thermal | Linear (Stefan-Boltzmann) | A_rad = Q / (epsilon * sigma * T^4 - Q_env_absorbed); ~100-350 W/m^2 rejection | Thermal, All | ECSS-E-ST-31C |
| 102 | Radiator area -> Mass | Thermal->Structure | Linear | ~2-5 kg/m^2 (including OSR/MLI/structure) | Thermal, Structure | -- |
| 103 | Radiator area -> Face allocation competition | Thermal<->Structure | Zero-sum | Radiator competes with SA, antenna, payload aperture for external faces | Thermal, Structure, Power, Comms | -- |
| 104 | Eclipse heater power -> Battery capacity | Thermal->Power | Linear | Heater demand during eclipse adds directly to battery sizing | Thermal, Power | -- |
| 105 | Component temp limits -> Orbit constraints | Thermal->Orbit | Threshold | If component can't survive worst-case thermal, orbit may need to change | Thermal, Mission Analysis | -- |
| 106 | Component layout -> Thermal coupling | Thermal<->Structure | Conductive/radiative | Hot components next to cold-sensitive items = thermal management challenge | Thermal, Structure | -- |
| 107 | MLI mass -> Total mass budget | Thermal->Structure | Linear | MLI ~0.5-1.5 kg/m^2; covers most external surfaces | Thermal, Structure | -- |
| 108 | Heat pipe use -> Mass + cost | Thermal internal | Discrete step | Each heat pipe ~0.1-0.5 kg; needed if Q > conductive capacity of structure | Thermal | ECSS-E-ST-31-02C Rev.1 |
| 109 | Operating temp range -> Component selection | Thermal->All | Constraint | Military-grade: -40 to +85C; commercial: 0 to +70C; tighter range = more control needed | Thermal, EEE Components | ECSS-Q-ST-60C Rev.4 |
| 110 | Coating degradation (EOL) -> Margin | Thermal internal | Proportional | Alpha_s increases ~0.01-0.02/yr from UV+AO; drives BOL oversizing | Thermal | ECSS-E-ST-10-04C Rev.1 |
| 111 | Attitude mode -> Radiator orientation | AOCS->Thermal | Geometric | Sun on radiator face = catastrophic; thermal design assumes attitude control works | AOCS, Thermal | -- |
| 112 | Bus dissipation breakdown: EPS ~15%, AOCS ~10%, Comms ~30%, OBC ~10%, Payload ~35% | All->Thermal | Proportional | Each subsystem contributes heat to thermal balance | All subsystems, Thermal | -- |

---

## 7. STRUCTURE CASCADES

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 113 | Form factor -> Total mass limit | Structure internal | Discrete | 1U: 2kg; 3U: 4-6kg; 6U: 8-12kg; 12U: 20-24kg; micro: 50-100kg | Structure | CubeSat standard / launcher ICD |
| 114 | Total mass -> Launch cost | Structure->Cost | Linear | Rideshare: ~$5k-50k/kg LEO; dedicated: dominated by vehicle cost | Structure, Cost | -- |
| 115 | Total mass -> Propellant fraction (Tsiolkovsky) | Structure->Propulsion | Exponential | m_prop = m_dry * (exp(dV/Isp*g0) - 1); mass growth amplified exponentially | Structure, Propulsion | -- |
| 116 | Natural frequency -> Launch loads compatibility | Structure internal | Threshold | Must exceed launcher min freq (typically 30-100 Hz axial, 10-30 Hz lateral) | Structure | ECSS-E-ST-32C Rev.1, Launcher User Manual |
| 117 | Component mass/location -> CG position | Structure->AOCS | Summation | CG must be within launcher envelope; offset from geometric center drives torques | Structure, AOCS | -- |
| 118 | CG offset -> Thruster misalignment torque | Structure->Propulsion/AOCS | Linear | If thrust not through CG: T_disturbance = F * d_offset | Structure, Propulsion, AOCS | -- |
| 119 | Mechanism deployment -> Reliability | Mechanisms->PA | Discrete | Each deployment = potential single-point failure unless redundant | Mechanisms, PA | ECSS-E-ST-33-01C Rev.2 |
| 120 | Structure material -> Thermal conductivity | Structure->Thermal | Material property | Al: ~167 W/mK; CFRP: ~1-10 W/mK (through thickness); affects heat spreading | Structure, Thermal | -- |
| 121 | Volume packing -> Thermal coupling (conduction paths) | Structure->Thermal | Geometric | Tight packing = better conduction but less radiator view factor | Structure, Thermal | -- |
| 122 | Harness mass -> Total mass | Structure internal | Proportional | Harness ~ 5-10% of dry mass; longer paths = more harness | Structure | -- |
| 123 | Vibration isolation -> Mass addition | Structure internal | Proportional | Isolators add 0.1-1 kg but decouple payload from bus vibration | Structure, Payload | ECSS-E-HB-32-25A |
| 124 | Factor of safety -> Structural mass | Structure internal | Proportional | FoS of 2.0 (qual) vs 1.25 (flight): more conservative = heavier structure | Structure | ECSS-E-ST-32-10C Rev.2 |

---

## 8. PROPULSION CASCADES

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 125 | Mission dV budget -> Propellant mass | Mission->Propulsion | Exponential (Tsiolkovsky) | m_prop = m_dry * (exp(dV/(Isp*g0)) - 1); e.g., 100 m/s at 220s Isp = ~4.7% of dry mass | Propulsion, Systems | -- |
| 126 | dV components: orbit raise + maintenance + COLA + deorbit | Mission->Propulsion | Additive | Each mission phase adds to total dV; typically 50-200 m/s total for LEO mission | Propulsion, Mission Analysis | ECSS-U-AS-10C Rev.2 |
| 127 | Thruster type -> Power demand | Propulsion->Power | Discrete/extreme | Chemical: ~0W (valves only); Electric: 20-500W continuous during firing | Propulsion, Power | ECSS-E-ST-35-01C |
| 128 | Thruster type -> Tank volume | Propulsion->Structure | Discrete | Chemical: large tanks (low Isp, more propellant); Electric: small tanks (high Isp) | Propulsion, Structure | ECSS-E-ST-35-01C |
| 129 | Electric propulsion -> SA sizing | Propulsion->Power | Linear | EP thruster at 50W might double power demand during firing; SA must accommodate | Propulsion, Power | -- |
| 130 | Tank pressure -> Structure reinforcement | Propulsion->Structure | Linear (hoop stress) | MEOP * FoS drives wall thickness; pressurized systems need burst-pressure proof | Propulsion, Structure | ECSS-E-ST-32-02C Rev.1 |
| 131 | Plume impingement -> SA degradation | Propulsion->Power | Geometric/threshold | Hydrazine plumes deposit on SA if firing geometry is wrong; -1 to -5% power loss | Propulsion, Power | -- |
| 132 | Plume impingement -> Sensor contamination | Propulsion->Payload/AOCS | Geometric/threshold | Optical surfaces degraded by propellant condensation; star tracker blinding | Propulsion, Payload, AOCS | -- |
| 133 | Propellant mass -> Wet mass -> Launch cost | Propulsion->Cost | Linear cascade | Every kg propellant costs launch mass budget | Propulsion, Cost | -- |
| 134 | Thruster thrust level -> AOCS disturbance | Propulsion->AOCS | Proportional | High-thrust pulses create attitude disturbances; need simultaneous attitude control | Propulsion, AOCS | -- |
| 135 | Propulsion system mass fraction -> Available payload mass | Propulsion->Payload | Constraint | More propulsion mass = less payload mass in fixed total budget | Propulsion, Payload, Systems | -- |
| 136 | Mission lifetime -> Total impulse requirement | Mission->Propulsion | Linear | Longer mission = more station-keeping = more propellant | Mission Analysis, Propulsion | -- |
| 137 | Isp selection -> Propellant type -> Safety/handling | Propulsion->Operations | Discrete | Hydrazine (Isp ~220s): toxic handling; green propellants (Isp ~240s): simpler; cold gas (Isp ~70s): simplest | Propulsion, AIT, Safety | ECSS-Q-ST-40C Rev.1 |

---

## 9. GROUND SEGMENT CASCADES

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 138 | Number of ground stations -> Total contact time/day | Ground internal | Linear (approx) | Each polar GS adds ~4-8 contacts/day for LEO-SSO; ~40-80 min total per station | Ground Segment | ECSS-E-ST-70C |
| 139 | Contact time -> Data throughput capacity | Ground<->Comms | Linear | Throughput = DataRate * TotalContactTime * Efficiency(~80%) | Ground Segment, Comms | -- |
| 140 | Data throughput < Data generation | Ground->Payload | Constraint | If throughput insufficient, must reduce payload duty cycle | Ground Segment, Payload, Operations | -- |
| 141 | Station latitude -> Orbit inclination visibility | Ground<->Orbit | Geometric | Equatorial GS cannot see polar orbit passes near poles; polar GS sees all incl. | Ground Segment, Mission Analysis | -- |
| 142 | Ground processing latency -> User value/requirements | Ground->Mission | Application-specific | Near-real-time (<1hr) for disaster response; days acceptable for climate science | Ground Segment, Mission | -- |
| 143 | Number of stations -> Operations cost | Ground->Cost | Linear-to-sublinear | Each station ~$500k-5M/yr recurring; GS-as-a-service reduces to per-minute pricing | Ground Segment, Cost | -- |
| 144 | MCS complexity -> Operations team size | Ground->Cost | Proportional | Complex constellation ops = 10-20 FTE; single simple SC = 2-5 FTE | Ground Segment, Cost | ECSS-E-ST-70-11C |
| 145 | Autonomy level -> Ground contact dependency | Ground<->Software | Inverse | More on-board autonomy = less contact time needed = fewer ground stations | Ground Segment, Software, Comms | -- |
| 146 | Ground station antenna size -> Data rate achievable | Ground<->Comms | Proportional (gain) | Larger ground antenna = higher G/T = relaxes space segment TX requirement | Ground Segment, Comms | -- |
| 147 | TT&C + payload data on same band? | Ground<->Comms | Architecture decision | Shared: simpler but bandwidth constrained; Separate: more complex, more capable | Ground Segment, Comms | ECSS-E-ST-50C Rev.2 |

---

## 10. REQUIREMENTS CASCADES (Circular Dependencies)

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 148 | Mission requirement change -> System requirement update | Top-down | Cascade | Any change to mission objectives propagates through entire requirement tree | Systems, All | ECSS-E-ST-10-06C |
| 149 | System requirement -> Subsystem requirement allocation | Top-down | Decomposition | Budget allocated from system to subsystem (mass, power, pointing, etc.) | Systems, All | ECSS-E-ST-10C Rev.1 |
| 150 | Subsystem requirement -> Equipment specification | Top-down | Derivation | Component selection based on allocated budgets + margins | All subsystems | -- |
| 151 | Budget violation -> Requirement renegotiation | Bottom-up | Trigger | If subsystem cannot meet allocation, must request budget increase from system | All subsystems, Systems | ECSS-E-ST-10C Rev.1 |
| 152 | Budget increase for one -> Budget decrease for another | Lateral | Zero-sum (mass/power) | Total budget fixed by launcher/orbit; one subsystem gain = another's loss | Systems, All | -- |
| 153 | Requirement relaxation -> Design simplification -> Cost reduction | Top-down cascade | Nonlinear | Relaxing pointing from 0.01 to 0.1 deg eliminates star tracker + reduces AOCS cost by 30-50% | Systems, AOCS, Cost | -- |
| 154 | Performance margin erosion -> Design iteration | Circular | Iterative convergence | Margin policy: 30% (Phase A) -> 20% (Phase B) -> 10% (Phase C); tighter margins = less flexibility | Systems | ECSS-E-ST-10C Rev.1 |
| 155 | Interface requirement -> ICD -> Change propagation | Lateral | Trigger | Change to one side of interface propagates to other side | Systems, All | ECSS-E-ST-10-24C Rev.1 |
| 156 | Derived requirement traceability -> Impact assessment | Bidirectional | Graph traversal | Each requirement linked to parent; change to parent cascades to all children | Systems | ECSS-E-ST-10-06C |
| 157 | Requirement conflict detection -> Trade study trigger | Lateral | Threshold | When two requirements are contradictory, trade study required to resolve | Systems | ECSS-E-ST-10C Rev.1 |

---

## 11. SCHEDULE/COST CASCADES

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 158 | Component TRL -> Development time | TRL->Schedule | Inverse/exponential | TRL 9: 0 months dev; TRL 6: 12-24 months; TRL 3: 36-60 months | Cost, Schedule | ECSS-E-AS-11C (ISO 16290) |
| 159 | TRL -> NRE cost | TRL->Cost | Exponential | Low TRL: NRE dominates (10-100x recurring); High TRL: NRE minimal | Cost | NASA CEH, ECSS-M-ST-60C |
| 160 | COTS vs custom -> NRE + schedule | Decision->Cost/Schedule | Discrete | COTS: low NRE, 3-6 month procurement; Custom: high NRE, 12-36 month development | Cost, Schedule | -- |
| 161 | Mass -> Cost (CER) | Mass->Cost | Power law | Cost ~ k * Mass^x; x ~ 0.5-0.8 for spacecraft bus; varies by subsystem | Cost | NASA SSCM, USCM9 |
| 162 | Complexity -> Cost multiplier | Complexity->Cost | Multiplicative | PRICE-H complexity factor 1.0-10.0; heritage design ~1.5; novel ~5-8 | Cost | -- |
| 163 | Testing scope -> Cost + schedule | Test->Cost/Schedule | Proportional | Proto-flight: saves 1 model but higher risk; Qual + Flight: ~30-50% more cost | Cost, Schedule, PA | ECSS-E-ST-10-03 Rev.1 |
| 164 | Schedule pressure -> Risk | Schedule->Risk | Inverse | Compressed schedule = more parallel activities = more rework risk | Schedule, Risk | ECSS-M-ST-80C |
| 165 | Launch manifest -> Delivery date constraint | External->Schedule | Hard constraint | Miss delivery window = slip 3-12 months to next opportunity | Schedule | -- |
| 166 | Integration timeline -> Test facility booking | Schedule internal | Dependency | Thermal-vac, vibration table slots book 6-12 months ahead | Schedule | -- |
| 167 | Team size -> Burn rate -> Total cost | Org->Cost | Linear | Engineering labor ~ 60-70% of total Phase A-D cost for small missions | Cost | ECSS-M-ST-60C |
| 168 | Number of design iterations -> Schedule | Design->Schedule | Proportional | Each major redesign adds 2-6 months; good CE/CDF reduces iterations | Schedule, Systems | -- |

---

## 12. VERIFICATION CASCADES

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 169 | Model philosophy (PFM vs QM+FM) -> Cost + schedule | PA->Cost/Schedule | Discrete | QM+FM: ~1.5-2x hardware cost but lower risk; PFM: cheaper but no retest margin | PA, Cost, Schedule | ECSS-E-ST-10-03 Rev.1 |
| 170 | Test failure -> Redesign loop | Test->Schedule/Cost | Trigger (discrete event) | Major test failure: 3-12 month schedule impact + 10-50% cost overrun | PA, Schedule, Cost | -- |
| 171 | Margin policy by phase -> Early verification opportunity | Systems->Verification | Progressive | Larger early margins allow design to be verified against relaxed specs; tightened later | Systems, PA | ECSS-E-ST-10C Rev.1 |
| 172 | Verification method (IADT) -> Cost/schedule | Verification internal | Discrete | Inspection: cheap/fast; Analysis: medium; Demonstration: variable; Test: expensive/slow | PA | ECSS-E-ST-10-02C Rev.1 |
| 173 | Environmental test levels -> Qualification vs acceptance | PA internal | Discrete | Qual: higher levels (+3dB, +10C) than acceptance; drives equipment ratings | PA | ECSS-E-ST-10-03 Rev.1 |
| 174 | Test coverage -> Residual risk | PA->Risk | Inverse | More testing = less residual risk but diminishing returns above ~90% coverage | PA, Risk | -- |
| 175 | Component rating -> Test tailoring | PA internal | Discrete | Mil-spec components: less screening needed; COTS: extensive screening required | PA, EEE Components | ECSS-Q-ST-60C Rev.4 |

---

## 13. CROSS-CUTTING INTERCONNECTIONS (Multi-subsystem)

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 176 | Mass growth -> Power growth -> Thermal growth | A->B->C cascade | Compound | 1 kg mass increase often brings 1-3W power increase -> 1-3W more heat to reject | All, Systems | -- |
| 177 | Orbit change -> Cascade to ALL subsystems | Orbit->All | Global | Altitude change of 100km affects: GSD, eclipse, thermal, comms, radiation, drag, lifetime simultaneously | Mission Analysis, All | -- |
| 178 | Mode definition -> Power/thermal profile | Operations->Power/Thermal | Discrete states | Each operational mode (imaging, downlink, safe, eclipse) has unique power/thermal state | Operations, Power, Thermal | -- |
| 179 | Redundancy strategy -> Mass + cost + reliability | PA->Structure/Cost | Trade-off | Cold redundancy: +mass/cost, +reliability; No redundancy: lighter, cheaper, riskier | PA, Structure, Cost | ECSS-Q-ST-30C Rev.1 |
| 180 | Mission lifetime -> All degradation budgets | Mission->All | Linear scaling | Longer life = more radiation damage, more thermal cycling, more propellant, more SA degradation | Mission Analysis, All | -- |
| 181 | Constellation vs single SC -> Ground segment architecture | Architecture->Ground | Multiplicative | N satellites = N times contact opportunities but also N times ops complexity | Systems, Ground Segment | -- |
| 182 | EMC design -> Layout + harness routing + grounding | EMC->Structure/Power | Constraint network | EMC requirements drive physical separation, cable shielding, grounding scheme | EMC, Structure, Power | ECSS-E-ST-20-07C Rev.2 |
| 183 | Contamination control -> Outgassing + layout | PA->Thermal/Payload | Constraint | Optical payloads need molecular cleanliness; affects material selection + venting | PA, Thermal, Payload | ECSS-Q-ST-70-01C |
| 184 | Magnetic cleanliness -> Component selection + layout | AOCS->All | Constraint | Magnetometer-based attitude needs low SC magnetic dipole; constrains actuators/harness routing | AOCS, Power, Structure | -- |
| 185 | Single-event latch-up -> Power cycling capability | Radiation->Power/Software | Safety interlock | SEL protection requires per-component current limiting + watchdog power cycling | Radiation, Power, Software | ECSS-Q-ST-60-15C Rev.1 |
| 186 | Data latency requirement -> On-board processing -> Power/data | Mission->Software/Power | Architecture decision | On-board processing reduces downlink but adds computation power + heat | Mission, Software, Power, Thermal | -- |
| 187 | Deorbit compliance -> Propulsion OR drag device OR orbit selection | Regulation->Multiple | OR-constraint | 25-yr rule met by: lower orbit, propulsive deorbit, or drag sail; each has mass/complexity cost | Mission Analysis, Propulsion, Mechanisms | ECSS-U-AS-10C Rev.2 |
| 188 | Thermal cycling -> Fatigue life -> Structural integrity | Thermal->Structure | Cumulative | ~5700 cycles/yr in LEO; solder joints, adhesive bonds affected over 5+ year missions | Thermal, Structure | ECSS-E-ST-32C Rev.1 |
| 189 | Power bus transients -> AOCS sensor noise | Power->AOCS | EMC coupling | Switching regulators create ripple that can couple into magnetometer measurements | Power, AOCS, EMC | ECSS-E-ST-20-07C Rev.2 |
| 190 | Satellite angular rate -> Comms Doppler compensation | AOCS->Comms | Proportional | Tumbling SC has variable Doppler; comms receiver must track; drives receiver complexity | AOCS, Comms | -- |

---

## 14. ADDITIONAL INTERCONNECTIONS (to reach 200+)

| # | Connection | Direction | Nature | Sensitivity | Positions | Standard |
|---|-----------|-----------|--------|-------------|-----------|----------|
| 191 | Orbit repeat cycle -> Revisit time -> User value | Orbit->Mission | Discrete | Exact repeat orbit (e.g., 16-day for Landsat) drives orbit selection precisely | Mission Analysis | -- |
| 192 | Launch vehicle vibration spectrum -> Component qualification levels | External->PA | Envelope | Launcher environment defines min qual levels for all hardware | PA, Structure | ECSS-E-ST-10-03 Rev.1 |
| 193 | Solar cell efficiency -> SA area (inverse) | Power internal | Inverse | Triple-junction GaAs ~30% vs Si ~17%; GaAs needs 43% less area but 3-5x cost | Power | ECSS-E-ST-20-08C Rev.2 |
| 194 | Battery temperature -> Capacity + life | Thermal->Power | Nonlinear | Li-ion optimal 10-30C; <0C: capacity drops 20-40%; >45C: accelerated degradation | Thermal, Power | -- |
| 195 | On-board computer performance -> Software complexity -> Power | OBC->Software/Power | Proportional | More MIPS = more power; LEON3: ~1W; ARM Cortex: ~0.3W; FPGA: 2-10W | OBC, Software, Power | -- |
| 196 | Attitude determination accuracy -> Orbit determination accuracy | AOCS<->Navigation | Coupled | GPS needs attitude for antenna pointing; attitude uses GPS for timing | AOCS, Navigation | -- |
| 197 | Solar array current -> Magnetic dipole -> AOCS disturbance | Power->AOCS | Proportional | SA wiring loops create magnetic moment; ~0.01-0.1 Am^2 per amp-turn | Power, AOCS | -- |
| 198 | Thermal expansion -> Optical alignment -> Payload performance | Thermal->Structure->Payload | Proportional | Al CTE ~23 ppm/K; 10K range over 1m structure = 230 um misalignment | Thermal, Structure, Payload | -- |
| 199 | Propellant slosh -> AOCS disturbance | Propulsion->AOCS | Dynamic/resonance | Liquid slosh couples with attitude control; baffles add mass but damp oscillations | Propulsion, AOCS, Structure | -- |
| 200 | Ground ops concept -> On-board autonomy -> Software complexity -> V&V cost | Ground->Software->Cost | Cascade | More autonomy = less ground ops cost but more software dev + verification cost | Ground, Software, Cost, PA | ECSS-E-ST-70-11C |
| 201 | Inter-satellite link -> Constellation design -> Orbit selection | Comms->Mission | Architecture | ISL reduces ground station dependency but adds mass/power/complexity per SC | Comms, Mission Analysis | -- |
| 202 | Atomic oxygen (LEO) -> Material selection -> Mass + cost | Environment->Materials | Threshold | AO flux at 400km erodes some polymers; Kapton needs coating; drives material choice | Materials, Structure | ECSS-E-ST-10-04C Rev.1 |
| 203 | Solar pressure -> Attitude disturbance | Environment->AOCS | Proportional | T_srp = P_solar * A * d_cp-cg * (1+reflectivity); significant for large SA | AOCS | -- |
| 204 | Gravity gradient -> Attitude stability | Orbit->AOCS | Proportional to inertia difference | T_gg = 3*mu/(2*R^3) * |Iz-Ix| * sin(2*theta); drives passive stability for elongated SC | AOCS | -- |
| 205 | Launch loads -> Component mounting design -> Mass | Structure internal | Proportional | Higher g-loads (e.g., 15g axial) require stronger brackets -> more mass | Structure | ECSS-E-ST-32C Rev.1 |
| 206 | Orbital debris environment -> Shielding/avoidance -> Mass/propulsion | Environment->Structure/Propulsion | Probabilistic | MMOD shielding adds mass; COLA maneuvers consume propellant (~5 m/s/yr at ISS altitude) | Structure, Propulsion | ECSS-U-AS-10C Rev.2 |
| 207 | System power budget violation -> Mode restriction | Power->Operations | Constraint | If power negative in any mode, that mode duration must be restricted or eliminated | Power, Operations | -- |
| 208 | Data budget violation -> Imaging plan restriction | Comms->Operations | Constraint | If data exceeds downlink, must reduce imaging time per orbit | Comms, Payload, Operations | -- |
| 209 | Pointing budget roll-up -> Overall performance | AOCS/Structure/Thermal | RSS summation | Total pointing error = RSS(attitude knowledge + control + alignment + thermal distortion) | AOCS, Structure, Thermal | ECSS-E-ST-60-10C |
| 210 | Worst-case analysis (WCA) -> Design margins -> Mass growth | PA->All | Multiplicative | WCA reveals if margins are consumed; triggers redesign or descope | PA, All | ECSS-E-ST-10C Rev.1 |
| 211 | Reliability allocation -> Redundancy -> Mass + cost + power | PA->All | Discrete/multiplicative | R = 0.95 over 5 years might require dual-string comms (2x mass/cost for that subsystem) | PA, All | ECSS-Q-ST-30C Rev.1 |
| 212 | Configuration control -> Change impact assessment -> All budgets | Management->All | Process trigger | Every approved change requires re-evaluation of mass, power, thermal, link budgets | Configuration, All | ECSS-M-ST-40C Rev.1 |
| 213 | Integration sequence -> Panel access -> Thermal/harness design | AIT->Structure/Thermal | Constraint | Components integrated first are hardest to access later; drives panel design | AIT, Structure | -- |
| 214 | Qualification by heritage -> Reduced testing -> Cost/schedule savings | PA->Cost/Schedule | Discrete | If component is flight-proven in similar environment, delta-qualification suffices | PA, Cost, Schedule | ECSS-E-ST-10-03 Rev.1 |
| 215 | SA deployment -> Moment of inertia change -> AOCS reconfiguration | Mechanisms->AOCS | Step function | Post-deployment inertia may be 2-10x stowed value; AOCS gains must adapt | Mechanisms, AOCS | -- |
| 216 | Orbit altitude -> Atomic oxygen fluence -> Surface degradation rate | Orbit->Materials | Exponential | AO fluence: ~10^21 atoms/cm^2/yr at 400km; ~10^19 at 800km | Mission Analysis, Materials | ECSS-E-ST-10-04C Rev.1 |
| 217 | Power system topology (DET vs MPPT) -> Efficiency + mass + complexity | Power internal | Architecture decision | DET: simpler, lighter, ~85% eff; MPPT: complex, heavier, ~93% eff; crossover at ~50W | Power | -- |
| 218 | Downlink frequency -> Ground station cost | Comms->Ground/Cost | Discrete | UHF ground antenna: ~$10k; S-band: ~$50-200k; X-band: ~$200k-1M; Ka: ~$500k-5M | Comms, Ground Segment, Cost | -- |
| 219 | Constellation size -> Per-unit cost reduction (learning curve) | Architecture->Cost | Power law | Learning curve: unit N cost ~ first unit * N^(log(LC)/log(2)); LC ~85-95% for space | Cost | NASA CEH |
| 220 | End-of-life disposal -> Passivation requirement -> Propulsion design | Regulation->Propulsion | Constraint | Must deplete energy sources (batteries, pressure) at EOL; needs controlled venting | Propulsion, Power | ECSS-U-AS-10C Rev.2 |

---

## Summary of Governing Standards (Key References)

| Domain | Primary ECSS Standard | Scope |
|--------|----------------------|-------|
| System Engineering | ECSS-E-ST-10C Rev.1 | SE general requirements, budgets, margins, trade-offs |
| Requirements | ECSS-E-ST-10-06C | Technical requirements specification |
| Verification | ECSS-E-ST-10-02C Rev.1 | IADT method, verification control |
| Testing | ECSS-E-ST-10-03 Rev.1 | Environmental and functional test requirements |
| Space Environment | ECSS-E-ST-10-04C Rev.1 | Radiation, AO, MMOD, plasma environment definition |
| Radiation Calculation | ECSS-E-ST-10-12C + Corr.1 | TID/dose-depth curves, shielding analysis methods |
| Interface Management | ECSS-E-ST-10-24C Rev.1 | IRD, ICD, IDD content and process |
| EPS General | ECSS-E-ST-20C Rev.2 | Electrical/electronic general requirements |
| Power Supply | ECSS-E-ST-20-20C | Power bus design, interface requirements, margins |
| Photovoltaics | ECSS-E-ST-20-08C Rev.2 | Solar array qualification, degradation, performance |
| EMC | ECSS-E-ST-20-07C Rev.2 | Conducted/radiated emission/susceptibility limits |
| Thermal General | ECSS-E-ST-31C | TCS design requirements, analysis, margins |
| Thermal Analysis | ECSS-E-ST-31-04C | Thermal model data exchange format |
| Structures General | ECSS-E-ST-32C Rev.1 | Structural design, loads, verification |
| Structural Safety | ECSS-E-ST-32-10C Rev.2 | Factors of safety, material allowables |
| Mechanisms | ECSS-E-ST-33-01C Rev.2 | Mechanism design, testing, life qualification |
| Propulsion General | ECSS-E-ST-35C Rev.1 | Propulsion general requirements |
| Liquid/Electric Prop | ECSS-E-ST-35-01C | Liquid and electric propulsion design |
| Communications | ECSS-E-ST-50C Rev.2 | TT&C architecture, link budget, frequency allocation |
| RF & Modulation | ECSS-E-ST-50-05C Rev.2 | Modulation schemes, spectral requirements |
| AOCS | ECSS-E-ST-60-30C | AOCS requirements, budgets, modes |
| Control Performance | ECSS-E-ST-60-10C | Pointing/stability budgets, performance specification |
| Star Sensors | ECSS-E-ST-60-20C Rev.2 | Star tracker performance specification |
| Ground Operations | ECSS-E-ST-70C | Ground segment requirements |
| Operability | ECSS-E-ST-70-11C | Space segment operability requirements |
| Dependability | ECSS-Q-ST-30C Rev.1 | RAMT budgets, reliability allocation |
| Radiation Hardness | ECSS-Q-ST-60-15C Rev.1 | RHA component selection, testing |
| Debris Mitigation | ECSS-U-AS-10C Rev.2 | 25-year deorbit rule (ISO 24113) |
| Cost & Schedule | ECSS-M-ST-60C | Cost/schedule management requirements |
| Risk | ECSS-M-ST-80C | Risk management process |
| Configuration | ECSS-M-ST-40C Rev.1 | Change control, baselines |
| TRL | ECSS-E-AS-11C (ISO 16290) | Technology readiness level definitions |

---

## NASA Equivalents (for cross-referencing)

| Topic | NASA Standard/Document |
|-------|----------------------|
| Systems Engineering | NASA/SP-2016-6105 Rev 2 (SE Handbook), NPR 7123.1 |
| Cost Estimation | NASA CEH v4.0 (12-step process, CERs) |
| Debris | NASA-STD-8719.14 (25-yr rule) |
| Radiation | NASA-HDBK-4002A |
| Structural | NASA-STD-5001B (structural design & test factors) |
| EMC | NASA-HDBK-4001A |
| Contamination | NASA-STD-6016 |

---

## Key Equations for Constraint Engine Implementation

These are the core parametric equations that drive propagation:

1. **GSD** = h * pixel_size / focal_length
2. **Eclipse fraction** = (1/pi) * arccos(sqrt(h^2 + 2*R_E*h) / ((R_E+h)*cos(beta)))
3. **Orbital period** = 2*pi * sqrt((R_E+h)^3 / mu)
4. **Free space path loss** = 20*log10(d) + 20*log10(f) + 32.44 [dB]
5. **Link margin** = EIRP - FSPL - L_atm + G/T - k - 10*log10(Rb) - Eb/N0_req
6. **Radiator area** = Q_dissipated / (epsilon * sigma * (T_rad^4 - T_sink^4))
7. **Battery energy** = P_eclipse_load * T_eclipse / (DoD * eta_discharge)
8. **SA area** = P_required / (eta_cell * S_flux * cos(theta) * (1-degradation))
9. **Propellant mass** = m_dry * (exp(dV / (Isp * g0)) - 1)
10. **Drag force** = 0.5 * rho(h) * v^2 * Cd * A_cross
11. **Gravity gradient torque** = (3*mu / (2*R^3)) * |Iz - Iy| * sin(2*theta)
12. **Antenna gain** = eta_a * (pi * D / lambda)^2
13. **Pointing budget RSS** = sqrt(sum(error_i^2)) for knowledge + control + alignment + thermal
14. **Cost CER** = K * mass^x * complexity^y (parametric model form)
15. **Orbital lifetime** ~ function(h, A/m, F10.7) via exponential atmosphere model

---

## Implementation Notes for Constraint Propagation Engine

1. **Bidirectional propagation**: Many connections are genuinely bidirectional (marked A<->B). The engine must detect and resolve circular dependencies through iterative convergence (fixed-point iteration) or simultaneous solution.

2. **Discrete vs. continuous**: Some parameters are continuous (mass, power, area) while others are discrete (component selection, form factor, frequency band). The engine needs both gradient-based propagation and discrete-event triggers.

3. **Margin management**: ECSS margins vary by phase (30% Phase A -> 10% Phase C). The engine should support configurable margin policies that tighten over time.

4. **Mode-dependent budgets**: Power and thermal budgets are mode-specific (imaging mode, downlink mode, safe mode, eclipse). The engine should maintain separate budget instances per mode and check ALL modes.

5. **Convergence**: The classic "mass snowball" (more mass -> more power -> more SA area -> more mass) requires damped iteration. Typical CDF tools converge in 5-15 iterations with 0.5-0.7 damping factor.

6. **Violation detection**: When a constraint is violated (budget exceeded, requirement breached), the engine should identify which upstream parameter changes can resolve it and rank them by system-level impact (sensitivity analysis / Jacobian).

---

Sources:
- [ESA Concurrent Design Facility](https://technology.esa.int/lab/concurrent-design-facility)
- [The ESA CDF: Concurrent Engineering Applied to Space Mission Assessments](https://www.researchgate.net/publication/292727292_The_ESA_Concurrent_Design_Facility_CDF_Concurrent_engineering_applied_to_space_mission_assessments)
- [Design Structure Matrix Applied to Integrated Concurrent Engineering](https://www.sciencedirect.com/science/article/abs/pii/S0094576509004433)
- [MDO Approach to Integrated Space Mission Planning and Spacecraft Design](https://arxiv.org/abs/2110.07323)
- [Hierarchical Planning Applied to Preliminary Design of CubeSats](https://incose.onlinelibrary.wiley.com/doi/10.1002/sys.21803)
- [Using the DSM for Space System Design](https://www.designsociety.org/publication/42452/Using+the+Design+Structure+Matrix+for+Space+System+Design)
- [OCDT - Open Concurrent Design Tool](https://ocdt.esa.int/)
- [ECSS-E-TM-10-25A (CDF Data Exchange Model)](https://en.wikipedia.org/wiki/ECSS-E-TM-10-25A)
- [CubeSat Power System Design Guide](https://pressbooks-dev.oer.hawaii.edu/epet302/chapter/5-5-power-generation/)
- [CubeSat ADCS Guide](https://pressbooks-dev.oer.hawaii.edu/epet302/chapter/7-7/)
- [CubeSat Link Budget](https://pressbooks-dev.oer.hawaii.edu/epet302/chapter/9-6-link-budget/)
- [Small Satellite Thermal Modeling Guide (DTIC)](https://apps.dtic.mil/sti/trecms/pdf/AD1170386.pdf)
- [NASA Small Spacecraft Thermal Control SOA](https://www.nasa.gov/smallsat-institute/sst-soa/thermal-control/)
- [NASA Ground Data Systems SOA](https://www.nasa.gov/smallsat-institute/sst-soa/ground-data-systems-and-mission-operations/)
- [Spacecraft Thermal Control (MIT OCW)](https://ocw.mit.edu/courses/16-851-satellite-engineering-fall-2003/e3a84cc153960fff8d55480fe228bbcc_l23thermalcontro.pdf)
- [Space Systems Cost Modeling (MIT OCW)](https://ocw.mit.edu/courses/16-851-satellite-engineering-fall-2003/48d9bf8fdee0a10cafa7578bac23d73f_l15_costmodellec.pdf)
- [GSD and Spatial Resolution (Eckhardt Optics)](https://www.eckop.com/applications/remote-sensing/ground-sampling-distance-and-spatial-resolution-of-remote-sensing-systems/)
- [Radiation Effects on Satellites (IntechOpen)](https://www.intechopen.com/chapters/70180)
- [ECSS Standards Active List](https://ecss.nl/standards/active-standards/)
- [NASA Estimating Life Cycle Cost of Space Systems](https://ntrs.nasa.gov/api/citations/20160001190/downloads/20160001190.pdf)
- [Subsystem Coupling Cost - AIAA](https://arc.aiaa.org/doi/10.2514/6.2002-176)