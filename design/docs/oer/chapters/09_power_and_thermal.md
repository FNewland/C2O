# Part II — Subsystem Design

# Chapter 9 — Electrical Power and Thermal Control

> **Recommended background.** SMAD4 Ch. 11.4 (power) and 11.5 (thermal); ECSS-E-ST-20C §5 (electrical); ECSS-E-ST-31C (thermal control); Patel, *Spacecraft Power Systems*, Ch. 3–4; Gilmore, *Spacecraft Thermal Control Handbook*, Vol. 1, Ch. 1–4. This chapter uses the orbit of Chapter 7 (period, eclipse fraction) and the mode-based power budget of Chapter 8 §8.4.3; the sizing equations are derived from first principles in Part V (§V.10–§V.12).

## Learning objectives

By the end of this chapter, you will be able to:

1. Size a solar array from mission power demand, eclipse profile, and degradation
2. Size a battery from eclipse energy demand, depth of discharge, and cycle-life requirements
3. Compute orbit-average power using duty-cycle analysis
4. Explain EPS architecture (DET vs PPT, MPPT, bus regulation) and articulate the physics of each
5. Perform first-order thermal balance analysis (hot case and cold case) with full radiative derivation
6. Select thermal control methods and apply ECSS thermal margins
7. Explain MLI construction, heat-pipe operation, and heater sizing
8. Check a power and thermal design for closure in every operational mode

---

## 9.1 Electrical power system architecture

*[Source: SMAD, Ch. 11.4; ECSS-E-ST-20C; Patel, Ch. 3]*

The EPS is the "utility company" of the spacecraft. It must continuously supply regulated power to all subsystems through every operational mode, including eclipse. Unlike terrestrial power systems, a spacecraft EPS cannot draw from a grid — the solar array, battery, and power-conditioning electronics must form a fully self-contained, autonomous energy system with zero maintenance for the mission lifetime. Figure 9.1 shows the reference architecture.

<svg viewBox="0 0 800 300" xmlns="http://www.w3.org/2000/svg" style="max-width:700px; font-family: sans-serif; font-size: 11px;">
  <!-- Solar Array -->
  <rect x="30" y="100" width="120" height="60" rx="4" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
  <text x="90" y="125" text-anchor="middle" fill="#92400e" font-weight="bold">Solar Array</text>
  <text x="90" y="142" text-anchor="middle" fill="#92400e" font-size="10">GaAs 29.5 %</text>
  <text x="90" y="155" text-anchor="middle" fill="#92400e" font-size="9">1361 W/m²</text>
  <!-- MPPT -->
  <rect x="200" y="100" width="100" height="60" rx="4" fill="#e0e7ff" stroke="#4f46e5" stroke-width="2"/>
  <text x="250" y="125" text-anchor="middle" fill="#3730a3" font-weight="bold">MPPT</text>
  <text x="250" y="142" text-anchor="middle" fill="#3730a3" font-size="10">Regulator</text>
  <line x1="150" y1="130" x2="200" y2="130" stroke="#64748b" stroke-width="2" marker-end="url(#arr9)"/>
  <!-- Bus -->
  <line x1="300" y1="130" x2="480" y2="130" stroke="#dc2626" stroke-width="3"/>
  <text x="390" y="120" text-anchor="middle" fill="#dc2626" font-weight="bold">Regulated Bus (3.3 V / 5 V / Batt)</text>
  <!-- Battery -->
  <rect x="330" y="200" width="120" height="55" rx="4" fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
  <text x="390" y="222" text-anchor="middle" fill="#166534" font-weight="bold">Battery</text>
  <text x="390" y="239" text-anchor="middle" fill="#166534" font-size="10">Li-ion, DoD 30 %</text>
  <line x1="390" y1="200" x2="390" y2="133" stroke="#16a34a" stroke-width="2"/>
  <text x="408" y="175" fill="#16a34a" font-size="9">charge/discharge</text>
  <!-- Loads -->
  <rect x="520" y="40" width="110" height="35" rx="4" fill="#dbeafe" stroke="#2563eb"/>
  <text x="575" y="62" text-anchor="middle" fill="#1e40af" font-size="10">Payload (SW)</text>
  <rect x="520" y="85" width="110" height="35" rx="4" fill="#dbeafe" stroke="#2563eb"/>
  <text x="575" y="107" text-anchor="middle" fill="#1e40af" font-size="10">AOCS (SW)</text>
  <rect x="520" y="130" width="110" height="35" rx="4" fill="#dbeafe" stroke="#2563eb"/>
  <text x="575" y="152" text-anchor="middle" fill="#1e40af" font-size="10">Comms TX (SW)</text>
  <rect x="520" y="175" width="110" height="35" rx="4" fill="#dbeafe" stroke="#2563eb"/>
  <text x="575" y="197" text-anchor="middle" fill="#1e40af" font-size="10">OBC (always on)</text>
  <rect x="520" y="220" width="110" height="35" rx="4" fill="#dbeafe" stroke="#2563eb"/>
  <text x="575" y="242" text-anchor="middle" fill="#1e40af" font-size="10">Heaters (thermo)</text>
  <!-- Switch lines -->
  <line x1="480" y1="57" x2="520" y2="57" stroke="#64748b" stroke-width="1.5"/>
  <line x1="480" y1="102" x2="520" y2="102" stroke="#64748b" stroke-width="1.5"/>
  <line x1="480" y1="147" x2="520" y2="147" stroke="#64748b" stroke-width="1.5"/>
  <line x1="480" y1="192" x2="520" y2="192" stroke="#64748b" stroke-width="1.5"/>
  <line x1="480" y1="237" x2="520" y2="237" stroke="#64748b" stroke-width="1.5"/>
  <line x1="480" y1="57" x2="480" y2="237" stroke="#64748b" stroke-width="1.5"/>
  <text x="490" y="30" fill="#64748b" font-size="10">Switched lines</text>
  <text x="490" y="42" fill="#64748b" font-size="9">(SW = switchable)</text>
  <defs><marker id="arr9" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#64748b"/></marker></defs>
</svg>

**Figure 9.1** — Reference CubeSat EPS: solar array, maximum-power-point tracker, regulated bus, battery, and switched load lines.

### 9.1.1 Solar cell physics

A photovoltaic cell converts photon energy into electrical energy via the photovoltaic effect. When a photon with energy $E = h\nu \geq E_g$ (where $E_g$ is the semiconductor bandgap) strikes the cell, it promotes an electron from the valence band to the conduction band, creating an electron–hole pair. The built-in electric field at the p–n junction sweeps carriers to opposite terminals, producing a voltage ($V_{oc}$) and current ($I_{sc}$).

**Single-junction vs multi-junction cells:**

A single-junction cell (e.g., silicon, $E_g = 1.12$ eV) can only absorb photons with $E \geq E_g$. Photons with $E < E_g$ pass through unabsorbed; photons with $E \gg E_g$ lose excess energy as heat (thermalisation loss). The theoretical maximum efficiency for a single-junction cell under AM0 (space) illumination is approximately 31 % (Shockley–Queisser limit).

Multi-junction (MJ) cells stack two or three p–n junctions of different semiconductor materials, each tuned to absorb a different portion of the solar spectrum:

| Cell technology | Structure | Bandgaps (eV) | AM0 efficiency | Temp. coefficient | Flight heritage |
|----------------|-----------|---------------|----------------|------------------|-----------------|
| **Monocrystalline Si** | Single junction | 1.12 | 16–18 % | −0.45 %/°C | Extensive (ISS, many LEO) |
| **GaAs single-junction** | Single junction | 1.42 | 22–24 % | −0.21 %/°C | Moderate |
| **InGaP/GaAs dual-junction** | 2-junction | 1.86 / 1.42 | 26–28 % | −0.20 %/°C | Moderate |
| **InGaP/GaAs/Ge triple-junction** | 3-junction (lattice-matched) | 1.86 / 1.42 / 0.67 | 28–30 % | −0.19 %/°C | Extensive (> 90 % of modern S/C) |
| **InGaP/GaAs/InGaAs IMM** | 3-junction (inverted metamorphic) | 1.86 / 1.42 / 1.0 | 32–33 % | −0.18 %/°C | Growing |

*[Source: vendor triple-junction cell datasheets; Green et al., "Solar Cell Efficiency Tables," Progress in Photovoltaics, v.62, 2024. Vendor products named in this chapter are representative examples, not endorsements.]*

**Why triple-junction GaAs dominates space:** The AM0 solar spectrum (above the atmosphere) is richer in UV and blue photons than the AM1.5 terrestrial spectrum. Triple-junction cells capture this energy across three bandgaps. The top cell (InGaP, $E_g = 1.86$ eV) absorbs blue/UV, the middle cell (GaAs, $E_g = 1.42$ eV) absorbs visible, and the bottom cell (Ge, $E_g = 0.67$ eV) absorbs near-IR. Each junction contributes voltage in series, while current is limited by the lowest-current junction (current-matching constraint).

**Temperature effects:** In orbit, solar cells operate at 40–80 °C depending on mounting and orbit. Cell efficiency decreases with temperature due to increased intrinsic carrier concentration (which reduces $V_{oc}$). The temperature coefficient for triple-junction GaAs is approximately −0.19 %/°C relative — meaning a cell rated at 29.5 % at 28 °C drops to approximately 28.5 % at 80 °C. This must be included in power budget calculations:

$$\eta_{\text{cell}}(T) = \eta_{\text{ref}} \times [1 + \beta_T (T - T_{\text{ref}})]$$

where $\beta_T \approx -0.0019$ /°C for triple-junction GaAs and $T_{\text{ref}} = 28$ °C (standard test conditions). (The subscript distinguishes this coefficient from the orbit β-angle of Chapter 7.)

**Degradation mechanisms:** Solar cells degrade in orbit due to:

- **Radiation damage:** Energetic protons and electrons (trapped in the Van Allen belts and from solar particle events) displace atoms in the crystal lattice, creating recombination centres that reduce minority-carrier lifetime and thus current. Degradation is characterised as equivalent 1 MeV electron fluence. Typical rates: 2–3 %/year in LEO, 5–8 %/year in MEO (through the proton belt), 1–2 %/year in GEO.
- **UV darkening:** Ultraviolet radiation darkens cover-glass adhesive over time, reducing transmission.
- **Micrometeoroid erosion:** Gradual pitting of cover glass reduces optical transmission.
- **Electrostatic discharge (ESD):** In GEO or polar orbits, differential charging can cause arcing between cells, permanently damaging interconnects.

Cover glass (typically ceria-doped borosilicate, 100–150 µm thick) mitigates radiation and UV effects. The combined degradation factor is:

$$L_d = (1 - \delta)^n$$

where $\delta = 0.025$ (2.5 %/year for triple-junction GaAs in LEO with standard cover glass) and $n$ = mission lifetime in years.

### 9.1.2 Body-mounted vs deployable solar arrays

**Body-mounted cells** are bonded directly to the spacecraft's external panels. They are the simplest and most reliable option (no deployment mechanism, no hinges, no drive motors) but are severely area-limited.

| Mounting | Advantages | Disadvantages | Typical power |
|----------|-----------|---------------|--------------|
| **Body-mounted** | No mechanism risk, no power for tracking, low mass, low cost | Limited area (satellite surface only), poor illumination geometry for nadir-pointing S/C, high cell temperature | 1U: ~2 W, 3U: ~7 W, 6U: ~12 W |
| **Fixed deployable** | 2–4× more area, better Sun angle, lower cell temperature (radiative cooling from back side) | Deployment mechanism (single point of failure), aerodynamic drag increase, structural dynamics | 3U: ~15–25 W, 6U: ~30–48 W |
| **Tracking deployable** | Optimal Sun incidence ($\cos\theta \approx 1$), maximum power | SADM (Solar Array Drive Mechanism) adds mass/cost/complexity, continuous power for motor | Large S/C: 100+ W |

**Real mission examples:**

- **Planet SuperDove (3U+):** Body-mounted + two fixed deployable wings. ~25 W BOL. The deployables are spring-hinged panels that fold against the 3U body during launch and deploy after ejection from the dispenser.
- **ASTERIA (6U, JPL):** Dual deployable arrays, 48 W BOL, triple-junction GaAs cells on commercial deployable panels.
- **ISS-deployed 1U CubeSats:** Body-mounted only, 2–3 W. Adequate for simple sensor missions with low duty cycles.

### 9.1.3 Architecture types

| Architecture | How it works (physics) | Efficiency | Complexity | Typical use |
|-------------|----------------------|-----------|-----------|------------|
| **DET** (Direct Energy Transfer) | SA connects directly to bus; a shunt regulator diverts excess current to a resistor bank (dissipated as heat) when SA output exceeds load. No series regulator between SA and bus. Voltage varies with illumination. | 80–85 % (shunt losses) | Low | Heritage GEO spacecraft, some CubeSats |
| **PPT / MPPT** (Peak Power Tracking) | A DC–DC converter (typically boost or buck-boost) between SA and bus continuously adjusts its input impedance to operate the SA at its maximum power point (MPP). Uses perturb-and-observe or incremental-conductance algorithm. Extracts 10–15 % more power than DET, especially at off-nominal temperatures and end of life. | 90–95 % | Medium | Most modern CubeSats |
| **Unregulated bus** | Battery connects directly to the power bus through protection FETs only. Bus voltage equals battery voltage (3.0 V at empty to 4.2 V at full per cell, or 6.0–8.4 V for 2S). Subsystems must tolerate voltage variation. | Highest (no regulator losses) | Lowest | Very simple CubeSats, 1U missions |
| **Regulated bus** | DC–DC converters create fixed voltage rails (3.3 V, 5 V, 12 V) from battery/SA input. Subsystems see constant voltage regardless of battery state. Adds ~5–10 % losses in regulators but greatly simplifies subsystem design. | Good (85–90 % overall) | Medium | Most CubeSat COTS EPS boards |

**MPPT physics:** A solar cell's I–V curve has a distinct "knee" where the maximum power ($P = I \times V$) is extracted. At open circuit ($I = 0$), voltage is maximum but power is zero. At short circuit ($V = 0$), current is maximum but power is zero. The MPP sits at approximately 75–80 % of $V_{oc}$ and 90–95 % of $I_{sc}$. Temperature shifts the I–V curve (higher $T$ moves $V_{oc}$ left), so the MPP moves. An MPPT controller dynamically tracks this point, typically updating every 0.1–1 s. Common CubeSat MPPT converters achieve 95–97 % tracking efficiency.

**Battery charge regulation:** The EPS must prevent overcharging (which causes lithium plating, gas generation and thermal runaway in Li-ion cells) and overdischarging (which causes copper dissolution from the negative current collector, permanently damaging the cell). Modern CubeSat EPS boards implement:

- **CC–CV charging:** Constant-current charging until cell voltage reaches 4.2 V, then constant-voltage taper until current drops below C/20
- **Under-voltage lockout:** Bus disconnect when cell voltage falls below 3.0 V (or 2.8 V for emergency)
- **Cell balancing:** For multi-cell series configurations (2S or higher), passive or active balancing circuits keep cells within 50 mV of each other
- **Temperature cut-offs:** Charging inhibited below 0 °C and above 45 °C (Li-ion charging below 0 °C causes lithium plating)

**CubeSat standard:** Most commercial EPS boards use MPPT + regulated bus with 3.3 V and 5 V rails, plus an unregulated battery rail (6.0–8.4 V for 2S Li-ion).

---

## 9.2 Solar array sizing

The sizing chain below is the canonical form used throughout this book; Part V §V.11 derives it from the orbit energy balance and shows its equivalence to the eclipse-fraction form found in some references.

> **Key equations — solar array sizing**
>
> **Step 1: Orbit-average power demand** (Chapter 8 §8.4.4):
> $$P_{\text{avg}} = \sum_{\text{modes}} P_{\text{mode}} \times f_{\text{duty,mode}}$$
>
> **Step 2: Array end-of-life power requirement.** During the sunlit arc ($t_{\text{sun}}$) the array must deliver the sunlit load through the daytime path and, at the same time, put back into the battery the energy the eclipse load ($P_{\text{ecl}}$ over $t_{\text{ecl}}$) took out, through the charge–store–discharge path:
> $$P_{\text{SA,EOL}} = \frac{\dfrac{P_{\text{sun}}\, t_{\text{sun}}}{\eta_{\text{sun}}} + \dfrac{P_{\text{ecl}}\, t_{\text{ecl}}}{\eta_{\text{ecl}}}}{t_{\text{sun}}}$$
> where $P_{\text{sun}}$ is the peak sunlit-mode demand (the array must cover the worst sunlit mode, not the average), $\eta_{\text{sun}}$ is the array-to-load path efficiency in sunlight (regulator only, ≈ 0.90) and $\eta_{\text{ecl}} = \eta_{\text{charge}} \times \eta_{\text{discharge}} \times \eta_{\text{regulator}}$ is the array-to-battery-to-load path efficiency (≈ 0.92 × 0.95 × 0.90 ≈ 0.79 for a typical CubeSat EPS). Using a lumped $\eta_{\text{ecl}} \approx 0.90$ is common in textbooks but slightly optimistic.
>
> **Step 3: Beginning-of-life power, accounting for degradation and temperature:**
> $$P_{\text{SA,BOL}} = \frac{P_{\text{SA,EOL}}}{L_d \times L_T}$$
> where $L_d = (1 - \delta)^n$ is the radiation degradation factor ($\delta = 0.025$/yr for TJ GaAs in LEO) and $L_T = 1 + \beta_T (T_{\text{cell}} - T_{\text{ref}})$ is the temperature derating factor ($\beta_T = -0.0019$/°C, $T_{\text{ref}} = 28$ °C, $T_{\text{cell}}$ typically 60–80 °C in LEO). For a cell operating at 65 °C: $L_T = 1 + (-0.0019)(65 - 28) = 0.930$ (7 % power loss from temperature).
>
> **Step 4: Array area:**
> $$A_{\text{SA}} = \frac{P_{\text{SA,BOL}}}{\eta_{\text{cell}} \times S \times \cos\theta \times f_{\text{pack}} \times f_{\text{cover}}}$$
> where:
> - $\eta_{\text{cell}} = 0.295$ (triple-junction GaAs efficiency at AM0, 28 °C — STC rating)
> - $S = 1361$ W/m² (solar constant at 1 AU, Kopp & Lean 2011)
> - $\theta$ = **Sun incidence angle on the array** (angle between the array normal and the Sun vector). It is 0° for a Sun-tracking array. For a body-fixed panel on a nadir-pointed spacecraft it is set by the orbit β-angle of Chapter 7: a panel whose normal is perpendicular to the orbit plane sees a constant $\theta = 90° - |\beta|$, while a panel whose normal lies in the orbit plane (the zenith face) sees $\cos\theta = \cos\beta\cos\nu$ varying through the sunlit arc, so its sunlit-arc average is used. A deployable wing canted toward the Sun on a Sun-synchronous orbit typically achieves an effective orbit-averaged $\theta$ of 20–25°.
> - $f_{\text{pack}} = 0.85$–$0.90$ (cell packing factor — fraction of panel area covered by cells; gaps for interconnects, edge clearance and harness routing)
> - $f_{\text{cover}} = 0.97$ (cover-glass transmission loss, typically 2–4 %)
>
> **Step 5: Array mass:**
> $$m_{\text{SA}} = A_{\text{SA}} \times \sigma_{\text{SA}} + m_{\text{mechanism}}$$
> where $\sigma_{\text{SA}}$ is the areal density of the panel: body-mounted (cells on Al substrate) ≈ 2.0–2.5 kg/m²; rigid deployable (Al honeycomb/CFRP) ≈ 1.5–2.0 kg/m²; flexible deployable ≈ 0.8–1.2 kg/m²; $m_{\text{mechanism}}$ (hinge, spring, hold-down) typically 0.1–0.3 kg per panel for CubeSats.

Figure 9.2 shows what the sizing equation is balancing: generation is a near-rectangular pulse over the sunlit arc, while the load is a stack of always-on bus power, heater power, and the short imaging and downlink peaks — some of which fall in eclipse and must be drawn from the battery.

![Power generation and stacked load profile over one orbit.](../assets/figures/fig_power_modes.png)

**Figure 9.2** — Top: solar-array generation across one orbit (sunlit arc and eclipse). Bottom: illustrative stacked load profile by subsystem, with imaging and downlink peaks superimposed on the always-on bus and heater loads. The array must deliver the sunlit load and recharge the eclipse energy within the sunlit arc.

> **Worked example — EOSat-3U solar array**
>
> **Given** (Chapter 7 §7.2 and Chapter 8 Table 8.4): 500 km Sun-synchronous orbit, $T = 94.6$ min, $t_{\text{sun}} = 58.8$ min, $t_{\text{ecl}} = 35.8$ min; peak sunlit demand $P_{\text{sun}} = 10.0$ W (downlink mode), $P_{\text{ecl}} = 3.5$ W; mission lifetime 3 years; cell temperature 65 °C; one deployable panel with effective orbit-averaged $\theta = 23°$; $\eta_{\text{sun}} = 0.90$, $\eta_{\text{ecl}} = 0.92 \times 0.95 \times 0.90 = 0.786$.
>
> **Step 2 — EOL array power:**
> $\dfrac{P_{\text{sun}}}{\eta_{\text{sun}}} = \dfrac{10.0}{0.90} = 11.11$ W $\qquad \dfrac{P_{\text{ecl}}\, t_{\text{ecl}}}{\eta_{\text{ecl}}\, t_{\text{sun}}} = \dfrac{3.5 \times 35.8}{0.786 \times 58.8} = \dfrac{125.3}{46.2} = 2.71$ W
>
> $P_{\text{SA,EOL}} = 11.11 + 2.71 = 13.82$ W
>
> **Step 3 — BOL power, 3-year degradation and temperature:**
> $L_d = (1 - 0.025)^3 = 0.9269$; $\quad L_T = 1 + (-0.0019)(65 - 28) = 0.930$
>
> $P_{\text{SA,BOL}} = \dfrac{13.82}{0.9269 \times 0.930} = \dfrac{13.82}{0.862} = 16.0$ W
>
> **Step 4 — Array area:**
> $A_{\text{SA}} = \dfrac{16.0}{0.295 \times 1361 \times \cos 23° \times 0.85 \times 0.97} = \dfrac{16.0}{0.295 \times 1361 \times 0.9205 \times 0.85 \times 0.97} = \dfrac{16.0}{304.7} = 0.0526$ m²
>
> This is approximately 23 cm × 23 cm — achievable with a single deployable panel on a 3U CubeSat (commercial 3U deployable wings provide up to ~0.06 m² each).
>
> **Step 5 — Array mass (deployable, rigid):**
> $m_{\text{SA}} = 0.0526 \times 1.8 + 0.15 = 0.095 + 0.15 = 0.25$ kg (panel + mechanism)
>
> **Comparison with Planet SuperDove:** The actual SuperDove uses body-mounted cells plus two deployable wings, achieving ~25 W BOL. The 16 W BOL from one panel calculated here is consistent — SuperDove's higher power supports continuous imaging plus S-band downlink simultaneously.
>
> **A caution on the inputs.** Chapter 12 §12.5.3 shows that the equipment-level imaging load comes to ≈ 10 W; the sizing here uses the 8 W parametric allocation of Table 8.4 (and the 10 W downlink peak) and must be re-run once equipment is selected — a typical CDF iteration.

Figure 9.3 generalises the calculation as a nomograph: for given cell efficiency, degradation, Sun angle and path efficiency, the required EOL array area is read directly from the orbit-average load and the eclipse fraction.

![Solar-array sizing nomograph.](../assets/figures/fig_solar_array.png)

**Figure 9.3** — Solar-array sizing nomograph following the §9.2 chain. Left: BOL array power against orbit-average load for three eclipse fractions (Steps 2–3, with $\eta_{\text{sun}} = 0.90$, $\eta_{\text{ecl}} = 0.79$ and $L_d L_T = 0.86$); the eclipse fraction raises the requirement because the eclipse energy must be recharged within the sunlit arc. Right: array area from Step 4, $A = P_{\text{BOL}}/(\eta_{\text{cell}} S \cos\theta f_{\text{pack}} f_{\text{cover}})$, for three Sun angles, with the EOSat-3U point (16.0 W BOL → 0.053 m² at θ = 23°) marked.

### 9.2.1 CubeSat array power reference

| Configuration | 1U | 3U | 6U | 12U |
|--------------|-----|-----|-----|------|
| Body-mounted only | ~2 W | ~7 W | ~12 W | ~20 W |
| Single deployable | ~4 W | ~15 W | ~30 W | ~55 W |
| Dual deployable | — | ~25 W | ~48 W | ~100 W |
| Quad deployable | — | — | ~80 W | ~180 W |

*[Source: vendor datasheets; ASTERIA 6U confirmed 48 W BOL; Dove/SuperDove confirmed ~25 W]*

---

## 9.3 Battery sizing

### 9.3.1 Li-ion cell chemistry and physics

All modern spacecraft batteries use lithium-ion (Li-ion) chemistry. During discharge, lithium ions migrate from the graphite anode (negative electrode) through an organic electrolyte and polymer separator to the lithium metal-oxide cathode (positive electrode), while electrons flow through the external circuit doing work. During charging, the process reverses.

**Common cathode chemistries used in space:**

| Chemistry | Cathode | Nominal voltage | Energy density | Cycle life (30 % DoD) | Thermal stability | Space heritage |
|-----------|---------|----------------|---------------|----------------------|-------------------|----------------|
| **LCO** (LiCoO₂) | Cobalt oxide | 3.7 V | 150–200 Wh/kg | ~10 000 | Moderate | ISS, many CubeSats (18650 cells) |
| **NMC** (LiNiMnCoO₂) | Nickel-manganese-cobalt | 3.7 V | 170–250 Wh/kg | ~5 000 | Moderate | Growing heritage |
| **LFP** (LiFePO₄) | Iron phosphate | 3.2 V | 90–120 Wh/kg | ~50 000 | Excellent | Niche (when cycle life is paramount) |
| **NCA** (LiNiCoAlO₂) | Nickel-cobalt-aluminium | 3.6 V | 200–260 Wh/kg | ~3 000 | Lower | Limited space heritage |

*[Source: Ratnakumar et al., NASA JPL; space-qualified cell datasheets; commercial 18650 specifications]*

**Cell form factors:**

- **18650 cylindrical:** 18 mm diameter, 65 mm long. The workhorse of CubeSat missions, 2500–3350 mAh per cell depending on type; energy 9–12 Wh per cell.
- **Pouch cells:** Custom dimensions, higher energy density (~250 Wh/kg) but require external structural support. Used in some 6U+ missions and all large spacecraft.
- **Prismatic cells:** Rigid case, intermediate between cylindrical and pouch. Used in some mission-specific designs.

**Cell configuration:**

Cells are arranged in series (S) to increase voltage and parallel (P) to increase capacity:

- **1S (single cell):** 3.0–4.2 V bus. Used for very simple 1U CubeSats.
- **2S (two in series):** 6.0–8.4 V bus. Standard for most CubeSats.
- **2S2P (two series, two parallel):** 6.0–8.4 V bus, double capacity (~38 Wh with four 18650 cells). Used for higher-energy missions.

**Protection circuits:** Every flight battery pack includes:

- **Cell voltage monitoring:** Per-cell voltage measurement to detect over/under-voltage
- **Over-current protection:** Current-sense resistors + MOSFET switches to disconnect at overcurrent (prevents short-circuit thermal runaway)
- **Temperature monitoring:** Thermistors on each cell; inhibit charging below 0 °C and above 45 °C
- **Heater circuit:** Kapton heater on the battery pack, thermostatically controlled, to maintain cells above minimum charging temperature during eclipse

**Capacity fade model:** Li-ion cells lose capacity over time due to solid-electrolyte-interphase (SEI) growth on the anode. A simplified calendar + cycling fade model:

$$C(t, N) = C_0 \times (1 - \alpha \sqrt{t}) \times (1 - \beta_c \cdot N \cdot \text{DoD}^{\gamma})$$

where $C_0$ = initial capacity, $t$ = time (years), $N$ = number of cycles, $\alpha \approx 0.02$ (calendar fade), $\beta_c \approx 3 \times 10^{-6}$, $\gamma \approx 2.1$ (cycling fade). For LEO at 30 % DoD, this gives approximately 5–8 % capacity loss per year — consistent with flight data from ISS battery replacements and CubeSat fleet telemetry.

### 9.3.2 Sizing equations

> **Key equations — battery sizing**
>
> **Required battery energy:**
> $$E_{\text{bat}} = \frac{P_{\text{ecl}} \times t_{\text{ecl}}}{\text{DoD} \times \eta_{\text{dis}}}$$
> where DoD is the maximum depth of discharge, $\eta_{\text{dis}} = 0.95$ (discharge efficiency, accounting for internal-resistance $I^2R$ losses), and $t_{\text{ecl}}$ is in hours.
>
> **Battery mass:**
> $$m_{\text{bat}} = \frac{E_{\text{bat}}}{e_{\text{specific}}}$$
> where $e_{\text{specific}} = 150$–$200$ Wh/kg for packaged Li-ion 18650 cells (cell-level energy density is higher, but packaging adds ~30 % mass).
>
> **Cycle life vs DoD** (Li-ion 18650, LCO chemistry):
>
> | DoD | Typical cycle life | Suitable mission duration | Annual eclipses (LEO, 15/day) |
> |-----|-------------------|--------------------------|-------------------------------|
> | 80 % | ~500 cycles | < 1 month | 450 |
> | 50 % | ~2 000 cycles | < 4 months | 1 800 |
> | 30 % | ~10 000 cycles | 1–2 years | 5 475 |
> | 20 % | ~30 000 cycles | 3–5 years | 10 950 |
> | 10 % | ~100 000 cycles | > 7 years | 38 325 |
>
> **Design rule of thumb:** For a multi-year LEO mission, start with 20–30 % DoD. For a short technology demonstration (< 6 months), 40–50 % DoD is acceptable and significantly reduces battery size, mass and cost.

Figure 9.4 shows the cycle-life curves behind this table for three Li-ion families, with the 1-, 5- and 10-year LEO cycle counts marked.

![Battery cycle life versus depth of discharge.](../assets/figures/fig_battery_dod.png)

**Figure 9.4** — Cycles to end of life versus depth of discharge for heritage LCO, aerospace NCA/NMC and LFP cells. Horizontal lines mark the cycle counts of 1-, 5- and 10-year LEO missions at ~15 eclipses per day; the 30 % DoD design point is typical for a multi-year mission.

> **Worked example — EOSat-3U battery**
>
> **Given:** $P_{\text{ecl}} = 3.5$ W, $t_{\text{ecl}} = 35.8$ min $= 0.597$ h, DoD $= 0.25$ (conservative for a 3-year mission), $\eta_{\text{dis}} = 0.95$.
>
> **Step 1 — Required battery energy:**
> $E_{\text{bat}} = \dfrac{3.5 \times 0.597}{0.25 \times 0.95} = \dfrac{2.09}{0.2375} = 8.8$ Wh
>
> **Step 2 — Apply the Phase A system margin (20 %, Table 8.3):**
> $E_{\text{bat,spec}} \geq 8.8 \times 1.20 = 10.6$ Wh. Specify **minimum 11 Wh**, ideally **20 Wh** for operational flexibility.
>
> **Step 3 — Verify cycle life:**
> 3-year mission at $1440/94.6 = 15.2$ orbits/day gives $3 \times 365 \times 15.2 \approx 16\,650$ eclipses. At 25 % DoD, Li-ion 18650 cells provide ~20 000 cycles. **Margin ≈ 20 %. Pass.**
>
> Including capacity fade: after 3 years, ~15–20 % capacity loss from calendar + cycling ageing. Effective DoD increases to $0.25/0.82 = 0.30$ — still within the 10 000-cycle regime. **Acceptable with monitoring.**
>
> **Step 4 — Battery mass:**
> $m_{\text{bat}} = \dfrac{20}{170} = 0.12$ kg (using 170 Wh/kg for packaged 18650 cells)
>
> **Step 5 — Battery volume:**
> Two 18650 cells in 2S1P: approximately 34 mL, fitting easily within a 3U stack.
>
> **Comparison with Planet SuperDove:** SuperDove carries approximately 20 Wh in a 2S2P configuration (4 cells), consistent with this sizing. The actual operating DoD is estimated at 10–15 % per eclipse, giving substantial cycle-life margin for the multi-year constellation replenishment cadence.

**Failure modes to watch for:**

- **Thermal runaway:** If a cell is overcharged, mechanically damaged, or experiences an internal short, the exothermic decomposition of the cathode material can lead to thermal runaway (self-heating > heat dissipation), potentially reaching 600+ °C. Mitigation: cell-level fuses, per-cell voltage monitoring, thermal cut-offs.
- **Lithium plating:** Charging below 0 °C causes metallic lithium to deposit on the anode surface rather than intercalating into graphite. This is irreversible, reduces capacity, and can cause internal shorts. Mitigation: battery heater + thermostat + software lockout.
- **Capacity imbalance:** In series configurations, the weakest cell limits the pack. If cells age at different rates, the weakest cell hits under-voltage lockout while others still have capacity. Mitigation: cell-balancing circuits, matched cell lots.

---

## 9.4 Thermal control system

*[Source: ECSS-E-ST-31C; Gilmore, Ch. 1–4; SMAD, Ch. 11.5]*

Figure 9.5 summarises the energy balance this section develops: four heat inputs (direct solar, Earth albedo, Earth infrared and the spacecraft's own electrical dissipation) and a single output, radiation to deep space, with the hot- and cold-case conditions that bound the design.

![Thermal energy-balance schematic of a CubeSat in LEO with solar, albedo, Earth-IR and internal inputs, radiation to space, and hot-case and cold-case annotations.](../assets/figures/fig_thermal_schematic.png)

**Figure 9.5** — Thermal energy balance of a CubeSat in LEO. Direct solar flux, Earth albedo and Earth infrared are absorbed according to the coating properties $\alpha_s$ and $\varepsilon$ and the view factors; internal dissipation adds the electrical power converted to heat; the only outlet is radiation to deep space, $\varepsilon \sigma A_{\text{rad}} T^4$. The hot case combines perihelion Sun, maximum dissipation, end-of-life coatings and maximum albedo; the cold case is eclipse in safe mode with beginning-of-life coatings and minimum Earth infrared (§9.4.5).

### 9.4.1 The physics of spacecraft thermal control

Spacecraft thermal control is fundamentally different from terrestrial thermal engineering because **there is no convection in vacuum**. The only heat transfer mechanisms are:

1. **Conduction:** Heat flow through solid material, governed by Fourier's law: $\dot{Q} = -kA \dfrac{dT}{dx}$. Critical within the spacecraft structure and between components and mounting surfaces.
2. **Radiation:** Heat transfer via electromagnetic radiation, governed by the Stefan–Boltzmann law: $\dot{Q} = \varepsilon \sigma A T^4$. This is the **only** mechanism for rejecting heat to the environment.

There is no convective cooling. A component that overheats cannot be cooled by a fan. All waste heat must be conducted to a radiating surface and then radiated to space. This is the central constraint of spacecraft thermal design.

### 9.4.2 Thermal environment in LEO

A spacecraft in LEO experiences four thermal inputs and one thermal sink:

| Source | Flux | Direction | Variability |
|--------|------|-----------|-------------|
| **Direct solar** | $S = 1361 \pm 1$ W/m² (at 1 AU) | Sun-facing surfaces only | Seasonal (±3.3 % due to Earth's orbital eccentricity: $S_{\text{perihelion}} = 1414$ W/m² in January, $S_{\text{aphelion}} = 1322$ W/m² in July) |
| **Earth albedo** | $\alpha_E \times S \approx 0.30 \times 1361 \approx 408$ W/m² | Earth-facing surfaces (nadir) | Varies with cloud cover, surface type (0.06 for ocean to 0.80 for fresh snow); orbit-average range 0.25–0.35 |
| **Earth infrared** | $q_{\text{IR}} \approx 240$ W/m² (orbit average) | Earth-facing surfaces (nadir) | Range 200–270 W/m² depending on latitude, season, cloud cover |
| **Internal dissipation** | $Q_{\text{int}} = P_{\text{dissipated}}$ | From electronics waste heat | Varies with operational mode; nearly all electrical power eventually becomes heat |
| **Deep space** (sink) | $T_{\text{space}} \approx 2.7$ K (CMB) | Zenith-facing radiator surfaces | Effectively 0 K for engineering purposes |

### 9.4.3 View factors

The fraction of a surface's radiative "view" that sees each thermal source is critical for accurate thermal modelling. For a flat nadir-facing surface in LEO:

$$F_{\text{Earth}} = \frac{1}{1 + (h/R_E)^2 + 2(h/R_E)} = \left(\frac{R_E}{R_E + h}\right)^2$$

where $h$ is the altitude and $R_E = 6378.137$ km. For a 500 km orbit: $F_{\text{Earth}} = (6378.137/6878.137)^2 = 0.860$. The nadir face sees 86 % Earth and 14 % deep space. The zenith face sees 100 % deep space (assuming no self-shadowing). Side faces see a mix.

At higher altitudes $F_{\text{Earth}}$ decreases: at 800 km it is 0.79, at 35 786 km (GEO) it is only 0.023 — which is why GEO thermal design is dominated by solar flux and internal dissipation, not Earth IR and albedo.

### 9.4.4 Thermal balance equation

> **Key equations — thermal equilibrium** (Part V §V.10)
>
> At steady state, the absorbed heat equals the radiated heat:
> $$Q_{\text{in}} = Q_{\text{out}}$$
>
> **Absorbed heat (expanded):**
> $$Q_{\text{in}} = \underbrace{\alpha_s \cdot A_{\text{sun}} \cdot S}_{\text{direct solar}} + \underbrace{\alpha_s \cdot A_{\text{alb}} \cdot F_{\text{alb}} \cdot \alpha_E \cdot S}_{\text{Earth albedo}} + \underbrace{\varepsilon \cdot A_{\text{IR}} \cdot F_{\text{IR}} \cdot q_{\text{IR}}}_{\text{Earth IR}} + \underbrace{Q_{\text{int}}}_{\text{internal dissipation}}$$
>
> **Radiated heat:**
> $$Q_{\text{out}} = \varepsilon \cdot \sigma \cdot A_{\text{rad}} \cdot T^4$$
>
> where:
> - $\alpha_s$ = solar absorptance of surface coating (dimensionless, 0–1)
> - $\varepsilon$ = infrared emittance of surface coating (dimensionless, 0–1)
> - $\sigma = 5.670 \times 10^{-8}$ W/m²/K⁴ (Stefan–Boltzmann constant)
> - $A_{\text{sun}}$, $A_{\text{alb}}$, $A_{\text{IR}}$, $A_{\text{rad}}$ = projected areas for each flux (m²)
> - $F_{\text{alb}}$, $F_{\text{IR}}$ = view factors to Earth for albedo and IR surfaces
> - $T$ = equilibrium temperature (K)
>
> **Note on $\alpha_s$ vs $\varepsilon$:** Solar absorptance ($\alpha_s$) is measured over the solar spectrum (0.2–2.5 µm, peak at 0.5 µm visible). Infrared emittance ($\varepsilon$) is measured over the thermal IR spectrum (3–50 µm, peak at ~10 µm for room-temperature objects). These are **different spectral ranges**, so $\alpha_s \neq \varepsilon$ for most real surfaces. This decoupling is the basis of all passive thermal control: by choosing the $\alpha_s/\varepsilon$ ratio, the designer controls the equilibrium temperature.
>
> **Solving for equilibrium temperature:**
> $$T = \left(\frac{Q_{\text{absorbed}} + Q_{\text{internal}}}{\varepsilon \sigma A_{\text{rad}}}\right)^{1/4}$$
>
> This equation is valid only for a single isothermal node (lumped-parameter model). For multi-node thermal models (needed for any real spacecraft), the heat balance is solved simultaneously for all nodes using numerical thermal-analysis software.

### 9.4.5 Hot case and cold case

| Case | Conditions | Design concern |
|------|-----------|----------------|
| **Hot case** | Maximum solar exposure ($S = 1414$ W/m², perihelion), all subsystems active (max $Q_{\text{int}}$), worst Sun angle (max $A_{\text{sun}}$), EOL coatings ($\alpha_s$ increased by UV darkening), max albedo (0.35) | Components exceed maximum operating temperature |
| **Cold case** | Eclipse (no solar), minimum power dissipation (safe mode, min $Q_{\text{int}}$), BOL coatings ($\alpha_s$ at its lowest), minimum Earth IR (200 W/m²), deep-space view | Components fall below minimum operating temperature |

**Design philosophy:** The thermal engineer designs to keep all components within their qualified temperature range under both worst-case hot and worst-case cold conditions, with ECSS-mandated margins applied.

### 9.4.6 Surface coatings — the passive thermal toolbox

| Coating | $\alpha_s$ (BOL) | $\alpha_s$ (EOL, 5 yr LEO) | $\varepsilon$ | $\alpha_s/\varepsilon$ (BOL) | Use case |
|---------|-----------|---------------------------|--------------|------------------------|----------|
| White paint (AZ-93, S13G-LO) | 0.14–0.20 | 0.25–0.35 | 0.89–0.92 | 0.16–0.22 | Radiator surfaces (stay cool; low solar absorption, high IR emission) |
| Black paint (Aeroglaze Z306) | 0.95 | 0.95 | 0.89 | 1.07 | Internal surfaces (maximise radiative exchange between components) |
| Gold tape (2 mil Kapton + VDA) | 0.22–0.25 | 0.25–0.30 | 0.03–0.05 | 5.0–7.5 | MLI outer layer, thermal isolation |
| Bare aluminium (polished) | 0.10–0.15 | 0.15–0.20 | 0.03–0.05 | 2.5–4.0 | Reflective surfaces, low emissivity |
| Alodine (chromate conversion on Al) | 0.35–0.40 | 0.40–0.50 | 0.12–0.16 | 2.5–3.0 | Moderate thermal control, structural surfaces |
| Anodised aluminium (clear or black) | 0.30–0.50 | 0.35–0.55 | 0.75–0.86 | 0.4–0.65 | CubeSat external structure (standard finish per CDS) |
| MLI blanket (effective) | 0.05–0.15 | 0.10–0.20 | 0.02–0.05 | ~3 | Thermal isolation of sensitive components |
| Solar cells (with cover glass) | 0.75–0.92 | 0.78–0.92 | 0.80–0.85 | ~1.0 | SA surfaces (high absorption is unavoidable; cells get hot) |
| OSR (Optical Solar Reflector) | 0.05–0.08 | 0.08–0.12 | 0.78–0.80 | 0.06–0.10 | High-performance radiators (large S/C, GEO) |

**Key design insight:** A surface with low $\alpha_s/\varepsilon$ (e.g., white paint: 0.2) stays cool because it reflects most solar energy but efficiently radiates thermal IR. A surface with high $\alpha_s/\varepsilon$ (e.g., gold tape: 6.0) stays warm because it absorbs solar energy but barely radiates. This is why white paint is used on radiators and gold or MLI for insulation. Figure 9.6 plots the equilibrium temperature of a flat plate in LEO against this ratio.

![Radiative thermal equilibrium versus α/ε.](../assets/figures/fig_thermal_balance.png)

**Figure 9.6** — Orbit-average equilibrium temperature of a flat plate in LEO as a function of $\alpha_s/\varepsilon$, with common coatings marked. White paint sits well below the electronics operating band, black paint near its upper edge; the dashed line is the eclipse-only (no Sun) temperature.

**Coating degradation:** UV radiation darkens most white paints over time, increasing $\alpha_s$ while leaving $\varepsilon$ nearly unchanged. The ratio $\alpha_s/\varepsilon$ therefore rises, and the surface runs hotter at EOL. The consequence for worst-case analysis is easy to get backwards: BOL white paint has the *lowest* $\alpha_s$, so the **cold case is most conservative with BOL properties**, while the **hot case is most conservative with EOL properties** after $\alpha_s$ has increased. Both cases must be run with the properties that make them worst.

### 9.4.7 MLI (multi-layer insulation) — construction and physics

MLI blankets are the most common thermal insulation on spacecraft. They work by minimising both radiation and conduction heat transfer through multiple reflective layers separated by low-conductance spacers.

**Construction (typical MLI blanket):**

1. **Outer cover:** 1 mil (25 µm) aluminised Kapton (VDA — vapour-deposited aluminium on one side). Provides mechanical protection and low solar absorptance.
2. **Inner reflective layers:** 10–20 layers of 0.25 mil (6 µm) double-aluminised Mylar (DAM). Each layer reflects IR radiation, and the vacuum gaps between layers have zero convection.
3. **Spacer material:** Dacron or Nomex netting between each DAM layer, preventing conductive contact between adjacent reflective sheets.
4. **Inner cover:** 1 mil aluminised Kapton, protecting the inner layers.

**Effective emissivity:** An ideal MLI blanket with $N$ reflective layers has an effective emissivity of:

$$\varepsilon_{\text{eff}} = \frac{1}{2/\varepsilon_{\text{inner}} + (N-1)(2/\varepsilon_{\text{layer}} - 1)}$$

For 20 layers of DAM ($\varepsilon_{\text{layer}} = 0.03$): $\varepsilon_{\text{eff}} \approx 0.002$. In practice, real MLI achieves $\varepsilon_{\text{eff}} = 0.01$–$0.03$ due to seams, penetrations (harness, mounting) and edge effects. The ratio of actual to theoretical performance is typically 2–5× worse.

**CubeSat MLI challenges:** CubeSats have limited surface area and many penetrations (connectors, antennas, sensors, solar cells), making it difficult to achieve good MLI performance. Most CubeSats in LEO do not use MLI — they rely on the moderate thermal environment (Earth IR provides a "warm floor") and surface coatings. MLI becomes essential for deep-space CubeSats (e.g., MarCO, CAPSTONE) or missions with sensitive payloads (IR detectors, laser systems).

### 9.4.8 Heater sizing

When passive thermal control cannot prevent a component from falling below its minimum temperature (typically during eclipse or safe mode), electrical heaters are required.

> **Key equations — heater sizing**
>
> **Required heater power** (to maintain minimum temperature during the worst cold case):
> $$P_{\text{heater}} = \varepsilon \sigma A_{\text{rad}} T_{\text{min}}^4 - Q_{\text{environment,cold}} - Q_{\text{internal,cold}}$$
> where $T_{\text{min}}$ is the minimum allowable temperature of the component (in kelvin).
>
> **Heater types for CubeSats:**
> - **Kapton foil heaters:** Etched-foil resistance elements laminated between Kapton sheets. Flexible, thin (0.2–0.5 mm), lightweight (2–10 g each). Typical power 0.5–5 W per heater. Bond directly to the component surface with pressure-sensitive adhesive.
> - **Cartridge heaters:** Cylindrical, inserted into drilled holes. Higher power density but heavier and less common on CubeSats.
>
> **Thermostat control:** Simple bimetallic thermostats switch heaters on/off at set temperatures (e.g., on at −5 °C, off at +5 °C). Mass ~2 g each. For higher reliability, software-controlled heaters using temperature-sensor feedback and EPS switches are preferred on modern CubeSats — but this requires the OBC to be running, which may not be the case in safe mode.

### 9.4.9 Heat pipes and thermal straps

**Heat pipes** are passive two-phase heat-transfer devices that transport large amounts of thermal energy with very small temperature differences. They are widely used on larger spacecraft and are beginning to appear on 6U+ CubeSats.

**How a heat pipe works:**

1. Working fluid (ammonia, methanol, or water) evaporates at the hot end (evaporator), absorbing latent heat
2. Vapour travels through the hollow pipe core to the cold end (condenser)
3. At the condenser, vapour releases latent heat and condenses back to liquid
4. Liquid returns to the evaporator via capillary action in a wick structure (sintered metal, axial grooves, or screen mesh)
5. The process is continuous, passive (no moving parts, no power), and can transport 10–100 W across 20–50 cm with < 5 °C temperature difference

**Thermal conductance of a heat pipe:** Effective thermal conductivity is 10 000–100 000 W/m/K (compared with copper at 400 W/m/K and aluminium at 237 W/m/K). A 6 mm diameter ammonia heat pipe can transport ~30 W over 30 cm with < 3 °C gradient.

**Thermal straps** are flexible conductive links (braided copper, graphite fibre, or pyrolytic graphite sheet) used to conduct heat between components that cannot be rigidly connected (e.g., across a hinge or between a vibration-isolated payload and the spacecraft bus). Typical conductance: 0.5–5 W/K.

| Heat transport method | Conductance | Mass | Power | Orientation sensitivity | CubeSat use |
|----------------------|-------------|------|-------|------------------------|------------|
| Aluminium conduction | ~0.5–2 W/K per path | Part of structure | 0 W | None | Always (inherent) |
| Copper thermal strap | 1–5 W/K | 10–50 g | 0 W | None | Occasional (6U+) |
| Heat pipe (ammonia) | 5–50 W/K | 20–100 g | 0 W | Gravity-dependent (must test in relevant orientation) | Rare (6U+, some 3U) |
| Pumped fluid loop | 50–500 W/K | 500+ g | 5–20 W | None | Large S/C only |

### 9.4.10 Thermal control methods summary

| Method | Type | Mass impact | Typical use | Key design parameter |
|--------|------|-------------|------------|---------------------|
| **Surface coatings** | Passive | Negligible | Always — select $\alpha_s/\varepsilon$ ratio per face | $\alpha_s/\varepsilon$ ratio |
| **MLI blankets** | Passive | 0.5–2.0 kg/m² | Insulate sensitive components from environment | Number of layers, $\varepsilon_{\text{eff}}$ |
| **Radiators** | Passive | Part of structure | Reject internal waste heat to deep space | Radiator area, $\varepsilon$, view to space |
| **Heaters** | Active | 0.005–0.02 kg each | Maintain minimum temperature during eclipse/safe mode | Power, thermostat set point |
| **Heat pipes** | Passive | 0.02–0.10 kg each | Transport heat from source to radiator | Working fluid, $Q_{\text{max}}$, orientation |
| **Thermal straps** | Passive | 0.01–0.05 kg each | Flexible conductive link across joints/hinges | Conductance (W/K) |
| **Louvres** | Active | 0.1–0.5 kg | Variable-conductance radiators (rare on CubeSats) | Open/close temperature range |

### 9.4.11 ECSS thermal margins

*[Source: ECSS-E-ST-31C, Table 5-1]*

| Level | Hot margin (above predicted max) | Cold margin (below predicted min) |
|-------|----------------------------------|-----------------------------------|
| **Qualification** | Predicted + 15 °C | Predicted − 15 °C |
| **Acceptance** | Predicted + 10 °C | Predicted − 10 °C |
| **Operating** | Predicted + 5 °C | Predicted − 5 °C |

These margins ensure that thermal-model uncertainties (typically ±5–10 °C for simplified models, ±2–5 °C for detailed correlated models) do not cause in-orbit temperature exceedances.

> **Worked example — EOSat-3U single-node thermal analysis**
>
> **Hot case (sunlit, peak mode, perihelion, EOL coatings):**
>
> Simplified single-node model. 3U CubeSat, nadir-pointing.
>
> - Sun-facing area (+Z, zenith-facing 3U panel): $A_{\text{sun}} = 0.034$ m²
> - SA surfaces (Sun-facing): $\alpha_s = 0.85$, $\varepsilon = 0.82$ (solar-cell properties)
> - Nadir face (−Z): $A_{\text{nadir}} = 0.034$ m², anodised Al ($\alpha_s = 0.45$ EOL, $\varepsilon = 0.82$)
> - Side faces (4×): $A_{\text{side}} = 4 \times 0.01$ m² $= 0.04$ m², anodised Al
> - Internal dissipation (peak mode, 10 W downlink — Table 8.4): $Q_{\text{int}} = 10.0$ W. Essentially all electrical power drawn by the loads ends as heat inside the spacecraft; the RF power actually radiated by the antenna (a watt or two) is the only exception and is conservatively ignored here.
>
> $Q_{\text{solar}} = 0.85 \times 0.034 \times 1414 = 40.9$ W — but much of this is converted to electricity by the cells, so the net thermal input through the array is $Q_{\text{solar,thermal}} = \alpha_s A S (1 - \eta_{\text{cell}}) = 0.85 \times 0.034 \times 1414 \times 0.705 = 28.8$ W
>
> $Q_{\text{albedo}} = 0.45 \times 0.034 \times 0.35 \times 1414 = 7.6$ W
>
> $Q_{\text{Earth IR}} = 0.82 \times 0.034 \times 270 = 7.5$ W (nadir face, hot-case Earth IR)
>
> Total $Q_{\text{in}} \approx 28.8 + 7.6 + 7.5 + 10.0 = 53.9$ W
>
> Total radiating area (all six faces, less the array area, which is a net absorber, and allowing for partial Earth blockage of the nadir face): $A_{\text{rad}} \approx 0.066$ m²; average emissivity $\varepsilon_{\text{avg}} \approx 0.82$
>
> $T_{\text{hot}} = \left(\dfrac{53.9}{0.82 \times 5.67 \times 10^{-8} \times 0.066}\right)^{1/4} = \left(\dfrac{53.9}{3.07 \times 10^{-9}}\right)^{1/4} = (1.756 \times 10^{10})^{1/4} = 364$ K $= +91$ °C
>
> **This exceeds most component limits!** However, this simplified calculation overestimates the temperature because it treats the satellite as a single isothermal node and lumps the solar-cell absorption on the zenith face into it. In practice:
> - The zenith face (solar cells) runs hotter than the bus
> - Internal components are conductively coupled to all faces, including the cold nadir face
> - A multi-node model typically predicts peak internal temperatures of +40 to +55 °C for this scenario
>
> **Thermal engineer's response:** If the single-node calculation exceeds 60 °C, a detailed multi-node thermal model is required. The simplified calculation is a screening tool, not a design tool.
>
> **Cold case (eclipse, safe mode, aphelion, BOL coatings):**
>
> - No solar flux, no albedo
> - Earth IR only: $Q_{\text{Earth IR}} = 0.82 \times 0.034 \times 200 = 5.58$ W (cold case: 200 W/m²)
> - Internal dissipation (safe mode, Table 8.4): $Q_{\text{int}} = 2.0$ W
> - Total $Q_{\text{in}} = 5.58 + 2.0 = 7.58$ W
>
> $T_{\text{cold}} = \left(\dfrac{7.58}{0.82 \times 5.67 \times 10^{-8} \times 0.070}\right)^{1/4} = \left(\dfrac{7.58}{3.25 \times 10^{-9}}\right)^{1/4} = (2.33 \times 10^{9})^{1/4} = 220$ K $= -53$ °C
>
> **This is too cold** for Li-ion batteries (min −20 °C operating, min 0 °C charging) and most COTS electronics (min −40 °C) — *if* the spacecraft had time to reach steady state.
>
> **Steady-state heater check.** To hold the whole spacecraft at $T_{\text{min}} = -10$ °C $= 263$ K would require
> $Q_{\text{heater}} = \varepsilon \sigma A_{\text{rad}} T_{\text{min}}^4 - Q_{\text{in}} = 3.25 \times 10^{-9} \times 263^4 - 7.58 = 15.6 - 7.58 = 8.0$ W
>
> An 8 W heater in eclipse would exceed the battery capacity. But this is an isothermal whole-spacecraft calculation: in reality the battery sits inside the bus, partially insulated by the structure and surrounding boards, and a targeted heater of 0.5–1.0 W on the battery pack, with some MLI wrapping, is typically sufficient. More importantly, the eclipse is only 36 minutes long and the structure's thermal mass prevents the satellite from approaching steady state at all.
>
> **Transient check.** In eclipse the net cooling rate is $Q_{\text{out}} - Q_{\text{in}}$. At eclipse entry, $T = 293$ K (+20 °C):
>
> $Q_{\text{out}} = 0.82 \times 5.67 \times 10^{-8} \times 0.070 \times 293^4 = 3.25 \times 10^{-9} \times 7.37 \times 10^{9} = 24.0$ W
>
> $Q_{\text{net cooling}} = 24.0 - 7.58 = 16.4$ W
>
> For a 5 kg spacecraft with aluminium-dominated thermal mass ($c_p \approx 900$ J/kg/K):
> $\Delta T = \dfrac{Q_{\text{net}} \times t}{m \times c_p} = \dfrac{16.4 \times 2150}{5.0 \times 900} = \dfrac{35\,260}{4500} = 7.8$ °C drop in 36 minutes
>
> So from +20 °C, the satellite cools to about +12 °C after one eclipse — well within limits (and the linear estimate is itself conservative, since $Q_{\text{out}}$ falls as $T^4$ as the spacecraft cools). **No heater needed for the bus; a battery heater only if the battery is thermally isolated from the bus.**
>
> **ECSS margin check — payload detector:**
> Predicted maximum temperature of the payload detector = 42 °C.
> - Operating limit = 50 °C. Margin = 50 − 42 = 8 °C > 5 °C. **Pass.**
> - Qualification test: must test at 42 + 15 = 57 °C. If the qualification limit is 60 °C: **Pass.**
>
> Predicted minimum temperature of the battery = −8 °C during the worst eclipse.
> - Operating limit = −10 °C. Margin = −8 − (−10) = 2 °C < 5 °C. **Fail — inadequate margin.**
> - **Action:** Add a 0.5 W survival heater with thermostat set to −5 °C, or add MLI around the battery pack.

---

## 9.5 Worked example: UniSat-1 power and thermal

Returning to UniSat-1, the 1U demonstrator of Chapter 1 §1.7, in the 400 km ISS orbit of Chapter 7 §7.7 (period 92.6 min, 56.5 min sunlight, 36 min eclipse).

**Power sizing: body-mounted only.** UniSat-1 uses body-mounted solar cells on all five Sun-exposed faces (the sixth face carries the deployment-switch interface). With no deployable panels, the power system is simpler, lighter and cheaper — but severely power-limited.

> **Worked example — UniSat-1 solar array**
>
> **Given:** Body-mounted cells on 5 faces of a 1U (100 × 100 mm each). $P_{\text{ecl}} = 0.5$ W (OBC only), $P_{\text{sun}} = 1.2$ W (science and downlink overlap avoided by scheduling). Mission lifetime 6 months. Cell temperature 55 °C (body-mounted cells run cooler on a 1U owing to good thermal coupling to the bus mass).
>
> **Step 1 — Effective illuminated area:**
> With passive magnetic attitude (slow tumble ~1°/s), on average only ~1.5 faces are well illuminated at any instant. Effective average area:
> $A_{\text{eff}} \approx 1.5 \times (0.10 \times 0.10) = 0.015$ m²
>
> **Step 2 — Array BOL power (with temperature derating):**
> $L_T = 1 + (-0.0019)(55 - 28) = 0.949$
>
> $P_{\text{SA,BOL}} = \eta_{\text{cell}} \times L_T \times S \times A_{\text{eff}} \times f_{\text{pack}} = 0.295 \times 0.949 \times 1361 \times 0.015 \times 0.80 = 4.57$ W (illuminated peak)
>
> **Step 3 — Orbit-average power available:**
> $P_{\text{avg,avail}} = P_{\text{SA,BOL}} \times \dfrac{t_{\text{sun}}}{T} \times \eta_{\text{EPS}} = 4.57 \times \dfrac{56.5}{92.6} \times 0.85 = 2.37$ W
>
> After 6-month degradation ($(1 - 0.025)^{0.5} = 0.987$): $P_{\text{avg,EOL}} = 2.37 \times 0.987 = 2.34$ W
>
> **Step 4 — Power demand (orbit average):** From Chapter 8 §8.5: $P_{\text{avg,demand}} = 0.68$ W.
>
> **Power margin:** $2.34 - 0.68 = 1.66$ W (**71 % margin**). Even with conservative geometry assumptions, the budget closes comfortably.
>
> **Note on body-mounted arrays and tumbling:** The key uncertainty in 1U body-mounted power is the attitude. With passive magnetic stabilisation the satellite aligns roughly with Earth's magnetic field, providing more predictable illumination than a random tumble; however, the effective area varies significantly around the orbit as the field direction changes with latitude. The 1.5-face average is conservative — a Monte Carlo simulation of illumination geometry over many orbits typically yields a more optimistic 1.7–1.9 effective-face average.

> **Worked example — UniSat-1 battery**
>
> **Given:** $P_{\text{ecl}} = 0.5$ W, $t_{\text{ecl}} = 36$ min $= 0.60$ h, DoD $= 0.50$ (acceptable for a 6-month mission: ~2 740 cycles), $\eta_{\text{dis}} = 0.95$.
>
> $E_{\text{bat}} = \dfrac{0.5 \times 0.60}{0.50 \times 0.95} = \dfrac{0.30}{0.475} = 0.63$ Wh
>
> With margin: specify minimum **10 Wh** — the smallest COTS CubeSat battery pack with flight heritage.
>
> **Cycle-count check:** 6 months at 15.5 orbits/day ≈ 2 800 eclipses. At 50 % DoD, Li-ion cells comfortably survive > 2 000 cycles. **Pass.**
>
> **Actual operating DoD:** With a 10 Wh battery and 0.63 Wh per eclipse, actual DoD = 0.63/10 = **6.3 %** per eclipse. At this DoD, cycle life exceeds 100 000 cycles. **Battery degradation is negligible** over the 6-month mission.
>
> **Key insight:** The 10 Wh battery is massively oversized for the actual eclipse demand. This is common in 1U missions — the minimum COTS battery available provides far more capacity than needed. The excess capacity provides excellent margin and enables recovery from anomalies (multiple missed sunlit periods).

**Thermal: passive only.** UniSat-1 uses no heaters, no MLI and no active thermal control. This is justified by three factors:

1. **Low altitude (400 km):** Strong Earth IR flux (~240 W/m²) provides a warm floor, preventing extreme cold cases
2. **Short mission (6 months):** No long-term coating degradation to worry about
3. **Tolerant components:** COTS electronics typically operate from −20 °C to +60 °C; the 400 km LEO thermal environment stays within −10 °C to +45 °C for a 1U with standard aluminium/anodised surfaces

> **Quick thermal check — UniSat-1 cold case (transient)**
>
> Worst eclipse, all subsystems off except OBC (0.5 W internal dissipation):
> - Earth IR absorbed: $\varepsilon \times A_{\text{nadir}} \times q_{\text{IR}} = 0.85 \times 0.01 \times 240 = 2.04$ W
> - Internal dissipation: 0.5 W
> - Total heat in: 2.54 W
>
> Steady-state temperature (if the eclipse were infinite):
> $T_{\text{steady}} = \left(2.54 / (0.85 \times 5.67 \times 10^{-8} \times 0.045)\right)^{1/4} = 195$ K $= -78$ °C
>
> **This looks alarming** — but the eclipse is only 36 minutes, and the thermal mass prevents the satellite from reaching steady state.
>
> **Transient analysis:** Starting at $T_0 = +20$ °C (293 K) at eclipse entry:
>
> $Q_{\text{rad,out}} = 0.85 \times 5.67 \times 10^{-8} \times 0.045 \times 293^4 = 2.17 \times 10^{-9} \times 7.37 \times 10^{9} = 16.0$ W
>
> Net cooling: $16.0 - 2.54 = 13.5$ W
>
> Linear estimate: $\Delta T = \dfrac{Q_{\text{net}} \times t}{m \times c_p} = \dfrac{13.5 \times 36 \times 60}{1.0 \times 900} = \dfrac{29\,160}{900} = 32$ °C
>
> The linear estimate is conservative — as the satellite cools, the radiated power drops as $T^4$, so the actual cooling slows. A more accurate estimate gives $\Delta T \approx 20$–$25$ °C, resulting in a minimum temperature of about −5 to −10 °C.
>
> **Conclusion:** The 1U at 400 km reaches approximately −5 to −10 °C during the worst-case eclipse, starting from a warm sunlit entry. This is within COTS operating limits (−20 °C to +60 °C for most components) and within the battery discharge range. **No heaters needed.** The short eclipse and the strong Earth IR flux at 400 km make passive thermal control viable for a 1U mission.

---

## 9.6 Real mission examples

### 9.6.1 Planet SuperDove EPS

| Parameter | Value | Design rationale |
|-----------|-------|-----------------|
| Form factor | 3U+, ~5 kg | Flock constellation; dispenser-compatible |
| SA configuration | Body-mounted + two deployable wings | ~25 W BOL needed for continuous imaging + S-band downlink |
| SA cells | Triple-junction GaAs | Standard space-grade, 29.5 % AM0 |
| Battery | Li-ion, ~20 Wh (2S2P 18650) | Supports ~3.5 W eclipse load for 35 min at < 20 % DoD |
| Bus voltage | Unregulated 7.2–8.4 V (2S) + regulated 3.3 V, 5 V | Standard CubeSat EPS architecture |
| Peak demand | ~18 W (imaging mode) | Multispectral imager + star tracker + reaction wheels + OBC |
| Orbit | 475 km SSO, ~94 min period | Sun-synchronous for consistent lighting |
| Eclipse | ~35 min max, ~3 W demand | OBC + AOCS only during eclipse; no imaging or downlink |
| Thermal | Body-mounted radiator panels + battery heater | Passive thermal control; battery heater for eclipse charging margin |

*[Source: Planet Labs conference presentations; Salas et al., "SuperDove Constellation," SSC 2021]*

### 9.6.2 CAPSTONE thermal design

NASA's CAPSTONE (12U, 25 kg) operates in a near-rectilinear halo orbit (NRHO) around the Moon with extreme thermal cycling:

- Perilune: strong Earth/Moon IR + solar
- Apolune: deep-space cold, long shadow periods (up to 12+ hours)
- Thermal control: MLI wrapping (10-layer DAM blankets), heaters on propulsion lines (to prevent propellant freezing), passive radiator panels with white paint (AZ-93)
- Battery heaters: 5 W total, thermostatically controlled, critical for survival during long eclipses
- Operating temperature range: −20 °C to +50 °C for electronics; propulsion lines maintained above +5 °C

*[Source: Advanced Space, "CAPSTONE Design Overview," SmallSat Conference 2022]*

---

## Summary

| Topic | Key takeaway |
|-------|-------------|
| Solar cell physics | Triple-junction GaAs (InGaP/GaAs/Ge) achieves 28–30 % AM0; multi-junction stacking captures a broader solar spectrum |
| Temperature effects | Cells lose ~0.19 %/°C (relative); operating at 65 °C costs ~7 % power vs STC |
| Degradation | Radiation damage: $(1-\delta)^n$, $\delta \approx 2.5$ %/yr LEO; cover glass mitigates proton/electron damage |
| EPS architecture | MPPT + regulated bus is the CubeSat standard; MPPT extracts 10–15 % more power than DET |
| SA sizing | $P_{\text{SA,EOL}} = (P_{\text{sun}} t_{\text{sun}}/\eta_{\text{sun}} + P_{\text{ecl}} t_{\text{ecl}}/\eta_{\text{ecl}})/t_{\text{sun}}$; derate for degradation $L_d$ and temperature $L_T$ |
| SA area | $A = P_{\text{BOL}} / (\eta_{\text{cell}} \cdot S \cdot \cos\theta \cdot f_{\text{pack}} \cdot f_{\text{cover}})$; θ from the array geometry and the orbit β-angle |
| Battery chemistry | Li-ion (LCO/NMC): 150–200 Wh/kg packaged; 3.0–4.2 V per cell; CC–CV charging |
| Battery sizing | $E = P_{\text{ecl}} \cdot t_{\text{ecl}} / (\text{DoD} \cdot \eta_{\text{dis}})$; DoD 20–30 % for multi-year LEO |
| Battery failure modes | Thermal runaway (overcharge), lithium plating (cold charge), capacity imbalance (series cells) |
| SA power reference | Body-mounted: 2–12 W; single deployable: 4–30 W; dual deployable: 25–48 W |
| Thermal physics | No convection in vacuum; radiation ($\varepsilon \sigma T^4$) is the only mechanism for heat rejection |
| Thermal balance | $Q_{\text{in}} = Q_{\text{out}}$; solve for $T = (Q/\varepsilon\sigma A)^{1/4}$ (single node); multi-node for real design |
| $\alpha_s/\varepsilon$ ratio | Low ratio = cold surface (radiator); high ratio = warm surface (insulation) |
| MLI construction | VDA Kapton outer + 10–20 DAM layers + Dacron spacers; $\varepsilon_{\text{eff}} = 0.01$–$0.03$ |
| Heater sizing | $P_{\text{heater}} = \varepsilon\sigma A T_{\text{min}}^4 - Q_{\text{env}} - Q_{\text{int}}$; Kapton foil heaters, thermostat control |
| Thermal margins | ECSS: ±5 °C operating, ±10 °C acceptance, ±15 °C qualification |
| Transient effects | Thermal mass ($mc_p$) prevents reaching steady state during short eclipses; a 1U at 400 km cools ~20–25 °C in a 36-min eclipse |

## Problems

1. **Array sizing.** A 3U Earth-observation CubeSat in a 550 km Sun-synchronous orbit (compute $T$, $t_{\text{sun}}$ and $t_{\text{ecl}}$ at β = 0 using Chapter 7) has a peak sunlit demand of 12 W and an eclipse load of 4 W. Size the solar array for a 4-year mission with cells at 70 °C and an effective Sun angle of 25°, showing all five steps. What array area and mass result?

2. **Path efficiency sensitivity.** Repeat the EOSat-3U worked example of §9.2 with the lumped $\eta_{\text{ecl}} = 0.90$ in place of 0.786, and with $\eta_{\text{sun}} = 1$ (no daytime regulator loss). By what percentage does the required BOL power change in each case? Which assumption would you accept at Phase A, and why?

3. **Sun angle and β.** For the EOSat-3U orbit (10:30 LTAN, assume β between 20° and 30° through the year), compare the orbit-averaged $\cos\theta$ of (a) a side-mounted panel whose normal is perpendicular to the orbit plane and (b) the zenith face. Which mounting gives more energy per orbit, and how does the answer change for a dawn–dusk (β ≈ 85°) orbit?

4. **Battery sizing and cycle life.** Size the battery for the spacecraft of Problem 1 at 20 % and 35 % DoD. For each, compute the number of eclipse cycles over 4 years and check against the cycle-life table. Which DoD would you choose, and what battery mass does it imply at 170 Wh/kg?

5. **Orbit-average closure.** Using the mode table of Chapter 8 Table 8.4 and the duty cycles of §8.4.4, confirm the orbit-average demand of 4.63 W. Then compute the orbit-average power the array of §9.2 actually delivers (BOL power × sunlit fraction × $\eta_{\text{sun}}$) and show whether the orbit-energy balance closes at BOL and at EOL.

6. **Hot-case screening.** Repeat the single-node hot-case calculation of §9.4.11 for a spacecraft whose zenith face is white-painted structure ($\alpha_s = 0.30$ EOL, $\varepsilon = 0.90$) instead of solar cells, with the array moved to a deployable wing that is thermally decoupled from the bus. What single-node temperature results, and what does the comparison tell you about where the array should be mounted from a thermal point of view?

7. **Transient cooling.** Integrate the eclipse cool-down of §9.4.11 numerically (time steps of 2 minutes, recomputing $Q_{\text{out}}$ at each step) and compare the result with the 7.8 °C linear estimate. Then repeat for the 1U UniSat-1 case and compare with the 20–25 °C quoted in §9.5.

8. **Heater sizing.** A battery pack of 0.15 kg (effective $c_p = 1000$ J/kg/K) is wrapped in MLI with $\varepsilon_{\text{eff}} = 0.03$ and radiating area 0.01 m², and enters eclipse at +15 °C. Estimate its cool-down over 36 minutes with no heater, and size a thermostat-controlled heater that holds it above 0 °C. What fraction of the eclipse energy budget of §9.3 does the heater consume?

9. **ECSS margins.** The predicted temperature range for a star tracker is −18 °C to +48 °C and its operating limits are −30 °C to +60 °C. Check the operating margin, state the acceptance and qualification test temperatures, and decide whether the design passes. If the qualification limit of the unit is +60 °C, what must change?

10. **UniSat-1 trade.** Suppose UniSat-1 adds a single deployable 1U panel (0.01 m², $\theta$ ≈ 30° average). Recompute the orbit-average power available and the margin. Then list the three new interfaces (Chapter 8 §8.3) and the one new failure mode the panel introduces, and argue whether the extra 1 W is worth it for a magnetometer mission.

## References

1. Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, Ch. 11.4 (EPS), Ch. 11.5 (Thermal). https://www.space.com/smad
2. ECSS, *ECSS-E-ST-20C Rev.1: Electrical and Electronic*, 2019. https://ecss.nl/standard/ecss-e-st-20c-electrical-and-electronic/
3. ECSS, *ECSS-E-ST-31C: Thermal Control*, 2008 (reissued 2020). https://ecss.nl/standard/ecss-e-st-31c-thermal-control/
4. Patel, M. R., *Spacecraft Power Systems*, CRC Press, 2005, Ch. 3–8. https://www.taylorfrancis.com/books/mono/10.1201/9781420038217/spacecraft-power-systems-mukund-patel
5. Gilmore, D. G. (ed.), *Spacecraft Thermal Control Handbook, Vol. 1: Fundamental Technologies*, 2nd ed., Aerospace Press, 2002. https://arc.aiaa.org/doi/book/10.2514/4.104503
6. Gilmore, D. G. (ed.), *Spacecraft Thermal Control Handbook, Vol. 2: Cryogenics*, 2003. https://arc.aiaa.org/doi/book/10.2514/4.104515
7. Ratnakumar, B. V. et al., *Lithium-Ion Batteries for Space*, NASA JPL, 2003. https://trs.jpl.nasa.gov
8. Kopp, G. & Lean, J. L., "A new, lower value of total solar irradiance," *Geophys. Res. Lett.* 38, 2011. https://doi.org/10.1029/2010GL045777
9. Green, M. A. et al., "Solar cell efficiency tables (version 62)," *Progress in Photovoltaics* 31, 2023. https://doi.org/10.1002/pip.3726
10. Salas, J. et al., "SuperDove constellation," Small Satellite Conference, 2021. https://digitalcommons.usu.edu/smallsat/
11. Advanced Space, "CAPSTONE design overview," Small Satellite Conference, 2022. https://digitalcommons.usu.edu/smallsat/
