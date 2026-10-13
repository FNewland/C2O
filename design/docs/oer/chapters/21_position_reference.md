# Part IV — Engineering Position Reference

This part is a background briefing for each engineering position at a concurrent-design table — the sixteen positions of Chapter 1 Table 1.4, including the Project Manager who chairs them. It is written for first-time CubeSat designers. For each position it covers:

- **Decisions you own.** What you have to choose, in what order.
- **What you need to know first.** Inputs you cannot decide without.
- **Formulas, charts and rules of thumb.** Pointers to the equations, tables and figures of Parts I–III (and the derivations of Part V) rather than restatements of them, plus the rules of thumb that are not written down anywhere else.
- **Common pitfalls.** What to watch for, especially the first time.
- **References.** Standards and texts for the position.

The briefings are two to four pages each and are self-contained. Read the one for the position you are about to take in full, and scan one adjacent to it: Power should scan Thermal, AOCS should scan Structures, Communications should scan Ground Segment, and everyone should scan Systems Engineer.

---

## Systems Engineer

You hold the budgets, the gate, and the authority to call a trade.

### Decisions you own

1. **Margin policy for this study.** You set the per-budget margin targets for the current phase. The two-level mass-margin schedule (equipment maturity margin plus system-level margin, tightening from Phase 0/A to Phase D) is Chapter 8 Table 8.3; the same phase-by-phase tightening applies to power, link and Δv, typically from about 25 %, 6 dB and 25 % in Phase A to 5 %, 3 dB and 5 % at Phase D (typical values; the mass schedule is Table 8.3).
2. **Budget closure decisions.** When power is over budget, you decide whether the team trades a payload duty cycle, a battery capacity, an array area, or an end-of-life lifetime.
3. **Cross-domain conflict resolution.** When AOCS wants more reaction-wheel mass and Thermal wants the same area for a radiator, you convene the affected positions and arbitrate.
4. **Gate-review readiness.** You judge whether the team is ready to enter the next review (Chapter 1 Table 1.3 lists the gates and their entry criteria; Chapter 16 §16.5 the evidence each one needs), and you sign the action items off.

### What you need to know first

- **Mission objectives** (SE process 1, Chapter 4) — the *why* drives the budgets you are closing.
- **The V-model** and where each position sits on it (Chapter 1 Figure 1.1 and Table 1.1).
- **The 17 NASA SEH processes** (Chapter 1 §1.3) — you will touch most of them every day.
- **The current lifecycle phase** (Chapter 1 Figure 1.4 and Table 1.2) — which sets the margin policy.

### Formulas, charts, rules of thumb

- **Margin definition and the budget-closure test** — Chapter 8 §8.4; the margin schedule is Table 8.3 and the mass-distribution picture is Figure 8.4. Your job is to keep every budget under the column for the current phase.
- **Interfaces** — the N² matrix of Chapter 8 §8.3 (Table 8.1, the type codes of Table 8.2, Figure 8.3). You own the matrix; the subsystem positions own the cells.
- **Requirements traceability** — Chapter 5 §5.4. Every budget line should trace to a requirement; every requirement to a verification method (Chapter 14).
- **Rule of thumb.** If a budget is within 2 % of its allocation at any review, treat it as *not closed*: the next equipment selection will move it by more than that.

### Common pitfalls

> **Watch out.** Resolving conflicts by averaging the two domains' requests *without* re-baselining the affected requirements is the classic systems-engineering failure mode. Always update the requirement before accepting the trade.

> **Watch out.** Margin is not slack. Margin is uncertainty insurance. If you give the margin to anyone — to AOCS for an extra wheel, say — record it as a depletion of margin in the change log, not as a new allocation.

> **Common mistake.** Letting individual subsystems consume their own margin so that nothing is held at system level. The system-level margin of Table 8.3 exists precisely because the subsystems' estimates are correlated.

### References

- NASA SEH (SP-2016-6105 Rev 2) — [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/)
- ECSS-M-ST-10C — Space project management — [https://ecss.nl/](https://ecss.nl/)
- ECSS-E-ST-10C — System engineering general requirements — [https://ecss.nl/](https://ecss.nl/)
- Wertz, Everett and Puschell, *Space Mission Engineering: The New SMAD* (2011), Ch. 2.
- Larson and Wertz, *SMAD*, Ch. 1, 22.

---

## Project Manager

You own the schedule, the money and the team's attention. The Systems Engineer decides what the design *is*; you decide when it is decided and by whom.

### Decisions you own

1. **Schedule baseline and priorities.** Milestones, dependencies, the critical path and where the schedule margin sits.
2. **Resource allocation.** Which position gets whose time this week, and when a position is over-subscribed.
3. **Review timing.** When the design is mature enough to hold the next gate (Chapter 1 Table 1.3) — and when it is not, however much the calendar says otherwise.
4. **Risk acceptance** (with engineering concurrence). You chair the risk review and decide which risks are accepted, mitigated or escalated (Chapter 15 §15.1).
5. **Scope changes.** Every stakeholder request for a change goes through you, with a cost and schedule impact attached before it is accepted.

### What you need to know first

- **The cost and schedule baseline** from the Cost Engineer (Chapter 16 §16.2 for the WBS, §16.4 for the cost-risk S-curve).
- **The risk register** (Chapter 15 §15.2) — the top five risks and their owners.
- **The interface agreements** between positions (Chapter 8 §8.3) — late interfaces are the usual cause of late schedules.
- **Stakeholder expectations** as captured in Chapter 4 §4.2, so that a change request can be judged against what was actually agreed.

### Formulas, charts, rules of thumb

- **Earned value.** Track work done against time spent and money spent; a project that reports progress by calendar rather than by completed products is already late.
- **Estimate at completion.** Chapter 16 §16.4 gives the P50/P80 treatment of cost risk; report the P80 to the sponsor and manage to the P50.
- **Review-board conduct** — Chapter 16 §16.6 gives the board roles, the reviewer question bank and the GO / NO GO / GO WITH ACTIONS outcomes.
- **Rule of thumb.** Schedule margin belongs at the *end* of the schedule, held by you; a milestone that is "on track" while its predecessors have consumed the float is not on track.

### Common pitfalls

> **Common mistake.** Not protecting the schedule margin — it is consumed by the early phases, where slipping feels cheap, and is missed in integration and test, where it is not.

> **Watch out.** Accepting scope creep without a schedule and cost impact assessment. "Small" additions to the telemetry list, the test programme or the data products are the ones that compound.

> **Common mistake.** Holding a review before the engineering products are mature, because the date was fixed months ago. A review that produces thirty actions has not saved time.

### References

- ECSS-M-ST-10C — Space project management — [https://ecss.nl/](https://ecss.nl/)
- NASA NPR 7120.5F — Space flight program and project management requirements — [https://nodis3.gsfc.nasa.gov/](https://nodis3.gsfc.nasa.gov/)
- Project Management Institute, *A Guide to the Project Management Body of Knowledge* (PMBOK Guide).

---

## Mission Analyst

You own the mission's relationship with physics: the orbit, the ground track, the lighting conditions, the contact times.

### Decisions you own

1. **Orbit type and altitude.** LEO / SSO / MEO / GEO / HEO / lunar. Altitude to balance science return, lifetime, drag, radiation and launch cost (Chapter 7 §7.3).
2. **Inclination.** Drives latitude coverage, ground-track repeat, and (with altitude) the Sun-synchronous condition.
3. **LTAN / LTDN** for SSO missions — drives the β-angle envelope and the eclipse season.
4. **Ground-station network.** Where to downlink, latency, coverage gaps (with Communications and Ground Segment).
5. **Manoeuvre plan.** When to phase, how to maintain station, when to deorbit (with Propulsion).

### What you need to know first

- The mission's **science target** — Sun-glint avoidance? polar coverage? continuous Earth observation?
- **Latitude band** of interest (polar Arctic monitoring forces an inclined or polar orbit).
- **Lifetime target** and the regulatory framework (FCC 5-year / IADC 25-year — Chapter 3 §3.6, Chapter 7 §7.3.2).
- **Launch availability** — a target launcher constrains both inclination and altitude.

### Formulas, charts, rules of thumb

- **Orbital period and velocity** — Chapter 7 §7.1.1; derived in Part V §V.2 and verified against known orbits in Figure D.1. For a 450 km orbit the period is 93.6 min; at 500 km it is 94.6 min.
- **Sun-synchronous condition** — pick $i$ so that the J₂-driven nodal regression matches the Earth's mean motion about the Sun (0.9856°/day): Chapter 7 §7.3.4, derived in Part V §V.4 with the inclination-versus-altitude curves of Figure D.2. At 600 km, $i \approx 97.8°$; at 700 km, $\approx 98.2°$.
- **Eclipse fraction** — the β-angle form of Chapter 7 §7.1.2, with the annual β envelope and the eclipse-fraction curves in Figure 7.2; derived in Part V §V.5. The worst case (longest eclipse) is at β = 0; above $\beta^* = \arcsin(R_E/(R_E+h))$ the orbit is fully sunlit.
- **Orbital lifetime** — the physics-based estimate of Chapter 7 §7.3.3 (a 3U at 400 km: roughly 9 months, 3 months to 2 years across the solar cycle; at 500 km, roughly 5 years). The rule of thumb and the lifetime chart of Chapter 3 §3.6.4 / Figure 3.2 are a first screen only; §7.3.3 explains why the rule overestimates by more than ten times below about 500 km.
- **Ground-station contact** — the pass-geometry formula and the 7.4 min maximum pass at 500 km / 10° mask are in Chapter 7 §7.4.1; the ground track is Figure 7.3; the pass profile is Chapter 17 Figure 17.2.
- **Transfers and deorbit** — Hohmann in Chapter 7 §7.5 and Figure 7.4; the deorbit Δv (112 m/s from 600 km to a 200 km perigee) feeds Chapter 12 §12.2.

### Common pitfalls

> **Common mistake.** Picking an altitude by habit and assuming it is debris-compliant. At 500 km a 3U decays in roughly five years (two to twelve across the solar cycle); at 650–700 km the same spacecraft can exceed the 25-year limit, and a 5-year rule changes the picture entirely. Always confirm with Chapter 7 §7.3.3 and a propagation (GMAT or equivalent).

> **Watch out.** Sun-glint angle for ocean-colour imaging changes with both season (β) and longitude. If your mission cares about Sun glint, build a year-long β / Sun-azimuth map before committing to an LTAN.

> **Watch out.** Eclipse fraction and β are not yours alone: Power sizes the battery on the longest eclipse (Chapter 9 §9.3) and Thermal sizes the cold case on it (Chapter 9 §9.4). Publish the β envelope early and tell them when it changes.

### References

- Curtis, *Orbital Mechanics for Engineering Students* (3rd ed.).
- Vallado, *Fundamentals of Astrodynamics and Applications* (4th ed.).
- SMAD4 Ch. 9 (orbit selection).
- Wertz, *Mission Geometry: Orbit and Constellation Design and Management* (2001).
- NASA GMAT (open source) — [https://software.nasa.gov/software/GSC-17177-1](https://software.nasa.gov/software/GSC-17177-1).

---

## Payload Lead

You own the science. The mission exists to do what your payload does, and every other subsystem ultimately serves yours.

### Decisions you own

1. **Payload concept and sensor type.** Optical / SAR / hyperspectral / radiometer / RF receiver / in-situ instrument.
2. **Aperture and spectral bands.** Drives resolution, SNR, mass.
3. **Operating concept.** Pushbroom vs whiskbroom vs framing; continuous vs target-cued.
4. **Data rate and data volume per orbit.** This drives Communications and OBDH (Chapter 11 §11.9, Chapter 12 §12.3).
5. **Calibration plan.** On-orbit sources, ground references, cadence.

### What you need to know first

- **The mission's measurable objective** (the MoP of Chapter 4 §4.3.3). For ocean colour you need certain bands at a certain SNR; for SAR a certain ground resolution and revisit; for AIS a certain detection probability.
- **Orbit altitude** from the Mission Analyst — drives slant range, GSD and coverage.
- **Mass and power available** — typically 30–50 % of the platform.

### Formulas, charts, rules of thumb

- **Ground sample distance.** The diffraction limit $1.22\,\lambda h/D$ and the pixel limit $p\,h/f$ are derived in Part V §V.9; the achievable GSD is the larger of the two. Figure D.3 plots both against aperture for visible imagers.
- **SAR antenna length.** The along-track antenna length must exceed about twice the desired azimuth resolution — a rule of thumb that sizes the deployable before any detailed design.
- **Data rate.** Pixels per line × bands × bit depth × line rate, then the daily volume against the downlink capacity of Chapter 11 §11.9 and Figure 11.6. Chapter 11 §11.8 shows the EOSat-3U case (956 MB/day capacity against 720 MB/day generated) and the UniSat-1 case, which does not close with one station.
- **Payload mass.** A heritage relationship of the form $M \approx 20\,D^{1.5} + 2$ kg (D in metres) is a first screen for optical payloads; replace it with a vendor figure as soon as one exists (Chapter 13).

### Common pitfalls

> **Common mistake.** Sizing the payload aperture for the diffraction limit while the detector pixels are too coarse to use it. Match the two — pixel-limited and diffraction-limited GSDs should be comparable.

> **Watch out.** Data volume per orbit grows with the aperture in two ways at once: more pixels and a faster line rate. Check the daily download capacity (Figure 11.6) before committing.

> **Watch out.** Your pointing and stability requirement is the single input AOCS most needs from you (Chapter 10 §10.4), and it is the one most often given late. Give a number, with a confidence, in the first design loop.

### References

- SMAD4 Ch. 9 (payload).
- Cracknell, *Introduction to Remote Sensing* (3rd ed.).
- Rees, *Physical Principles of Remote Sensing* (3rd ed.).
- Cumming and Wong, *Digital Processing of Synthetic Aperture Radar Data*.
- ECSS-E-ST-10-04C — Space environment — [https://ecss.nl/](https://ecss.nl/).

---

## Power Engineer

You own the orbit-by-orbit energy balance.

### Decisions you own

1. **Solar-array architecture.** Body-mounted vs deployable; gimballed vs fixed; technology (triple-junction GaAs vs Si).
2. **Solar-array area** — at end of life, accounting for degradation, the β-angle range and the Sun incidence angle.
3. **Battery capacity and DoD.** Cycle life vs eclipse depth.
4. **Bus voltage and PCDU architecture.** Single vs dual bus; regulated vs unregulated; MPPT topology (Chapter 9 §9.1, Figure 9.1).
5. **Power-mode duty cycle.** Maps to the ConOps modes (Chapter 18 Table 18.1).

### What you need to know first

- **Orbit** — drives the β-angle envelope and the eclipse fraction (Chapter 7 Figure 7.2).
- **Load by mode** from every subsystem, and the mode duty cycles, so that you can form the orbit-average and the peak sunlit load (Chapter 8 Table 8.4).
- **Mission lifetime** — drives cycle count and end-of-life degradation.

### Formulas, charts, rules of thumb

- **Solar-array sizing** — the five-step chain of Chapter 9 §9.2 (EOL power from the sunlit and eclipse loads, BOL power through the degradation and temperature factors, area through cell efficiency, Sun incidence angle, packing and cover-glass factors). Figure 9.2 shows what the balance is balancing; Figure 9.3 is the sizing nomograph. Part V §V.11 derives the chain and shows its equivalence to the eclipse-fraction form found in older references.
- **Battery sizing** — Chapter 9 §9.3, with the cycle-life-versus-DoD curves of Figure 9.4. A 25–30 % DoD design point gives the cycles needed for a multi-year LEO mission with margin; heritage LCO chemistry needs deeper de-rating, LFP gives more headroom but is less mass-dense. Part V §V.12.
- **Worked numbers** — EOSat-3U needs about 14 W of end-of-life array power and 0.053 m² of panel for a 10 W peak sunlit load (Chapter 9 §9.2); UniSat-1's are in §9.5.
- **Rule of thumb.** The array must cover the *worst sunlit mode*, not the orbit average; the battery must cover the *longest eclipse at the highest eclipse load*, not the typical one.

### Common pitfalls

> **Watch out.** Sizing the array for beginning of life will starve the battery at end of life. Always compute at EOL with realistic degradation (about 2.5 % per year for triple-junction GaAs in LEO, plus the temperature derating of Chapter 9 §9.2).

> **Common mistake.** Forgetting that the array only generates when the cells see the Sun — and that *which* cells see it changes through the year. β = 0° (Sun in the orbit plane) is the maximum-eclipse case: a zenith-facing body panel sees the Sun at normal incidence at orbit noon, but the eclipse is longest. At high |β| the eclipse shortens or disappears, but a panel whose normal lies in the orbit plane now sees the Sun at grazing incidence. Size across the whole β range of Figure 7.2, and state which panel and which season set the design point.

> **Watch out.** Thermal and you compete for the same external area — radiator or cells. Settle the allocation of each face in the first design loop, not the last.

### References

- ECSS-E-ST-20C — Electrical and electronic — [https://ecss.nl/](https://ecss.nl/)
- SMAD4 Ch. 11 (power).
- Patel, *Spacecraft Power Systems*.
- Brown, *Spacecraft Propulsion and Power Subsystems*.

---

## AOCS Engineer

You own the spacecraft's pointing.

### Decisions you own

1. **Pointing requirement** — knowledge vs control vs stability, per axis (Chapter 10 §10.1).
2. **Sensor suite** — Sun sensor / magnetometer / star tracker / GNSS receiver / IMU.
3. **Actuator suite** — magnetorquer / reaction wheel / thruster.
4. **Modes and transitions** — detumble, Sun acquisition, fine pointing, safe (with Operations: Chapter 18 §18.2).
5. **Momentum management plan** — how often, with what (Chapter 10 §10.5).

### What you need to know first

- **Pointing requirement** from the Payload Lead (for example 0.05° 1σ for a pushbroom imager).
- **Disturbance environment** at the chosen orbit (drag at 400 km vs 700 km; the magnetic field for a SSO) — Chapter 10 §10.2.
- **Spacecraft inertia tensor** — Structures gives you this, and it changes every time the layout does.

### Formulas, charts, rules of thumb

- **Pointing budget** — the root-sum-square of knowledge, control and alignment terms, Chapter 10 §10.4, drawn as a waterfall in Figure 10.3. In the EOSat-3U budget the alignment term dominates; improve the dominant term, not the sensor.
- **Disturbance torques** — gravity gradient, magnetic, solar pressure and drag in Chapter 10 §10.2; Part V §V.14 gives the order-of-magnitude drag estimate. For a 3U at 500 km the magnetic term dominates.
- **Wheel sizing** — momentum capacity from the disturbance torque, the interval between desaturations and a margin factor, Chapter 10 §10.3 and §10.5; Figure 10.4 shows the accumulation for a larger spacecraft. Note the slew-time result of §10.3: a small wheel is momentum-limited, not torque-limited, so the torque-only slew formula underestimates the time.
- **Rule of thumb.** Plan desaturation with the wheel. A wheel sized for fine pointing but not for unloading will saturate within a few orbits.

### Common pitfalls

> **Watch out.** Quaternion normalisation drift in flight software — even a 10⁻⁶ drift per second adds up. Renormalise every cycle.

> **Common mistake.** Designing for fine pointing without sizing the magnetorquers for desaturation. Plan the desaturation strategy at the same time as the wheel.

> **Watch out.** The Communications engineer's antenna choice depends on your pointing: a dish needs a fraction of its beamwidth, a patch tolerates tens of degrees (Chapter 11 Figure 11.2). Tell them what you can hold in *each* mode, including safe mode.

### References

- ECSS-E-ST-60-20C — Stars sensors; ECSS-E-ST-60-10C — Control performance — [https://ecss.nl/](https://ecss.nl/).
- Markley and Crassidis, *Fundamentals of Spacecraft Attitude Determination and Control*.
- Sidi, *Spacecraft Dynamics and Control*.
- SMAD4 Ch. 10.

---

## Thermal Engineer

You keep every component inside its operating range across the hot, cold and transient cases.

### Decisions you own

1. **Hot-case / cold-case envelope** — defined in terms of β-angle, season, eclipse and internal heating (Chapter 9 §9.4).
2. **Surface finishes (α, ε)** for each external panel and radiator.
3. **MLI vs heaters** — passive insulation vs active control.
4. **Heat-rejection topology** — radiator location and area.
5. **Thermal interfaces** — conductive paths to and from each component.

### What you need to know first

- **Operating temperature ranges** for every component (the battery is the strictest, typically −5 to +25 °C while charging).
- **Eclipse fraction and duration** from the Mission Analyst (Chapter 7 Figure 7.2).
- **Internal dissipation map** by mode from Power (Chapter 8 Table 8.4): the cold case is safe mode in the longest eclipse, the hot case is the highest dissipating mode at the smallest β.

### Formulas, charts, rules of thumb

- **Energy balance and radiative equilibrium** — Chapter 9 §9.4: solar, albedo and Earth-IR inputs, internal dissipation, radiated output; the equilibrium temperature as a function of α/ε is Figure 9.6, with common finishes marked. Part V §V.10 derives the flat-plate form and works a white-paint example.
- **Worked cases** — the EOSat-3U hot and cold cases, the steady-state heater power and the transient temperature drop over an eclipse are in Chapter 9 §9.4.11; UniSat-1 is in §9.5.
- **Rule of thumb.** The α/ε ratio is the dominant design knob: white paint (α/ε ≈ 0.16) sits well below the electronics band, black paint near its upper edge, bare polished aluminium far above it.
- **Rule of thumb.** Ten-layer MLI has an effective emittance ε* ≈ 0.03; fewer layers, less — and a CubeSat rarely has room for ten.

### Common pitfalls

> **Common mistake.** Using α and ε measured at room temperature for cold-case calculations — at −100 °C the emittance of many materials shifts. Cite the temperature of the source data.

> **Watch out.** MLI is rated by its effective emittance ε*, not by the base material.

> **Watch out.** The heater power you need in the cold case is Power's problem too: it lands in the eclipse load of Chapter 9 §9.3. Close that loop before the battery is sized.

### References

- ECSS-E-ST-31C — Thermal control — [https://ecss.nl/](https://ecss.nl/)
- Gilmore, *Spacecraft Thermal Control Handbook*, Vol. I and II.
- SMAD4 Ch. 12.

---

## Communications Engineer

You move the bits — both ways.

### Decisions you own

1. **Frequency band** — UHF / S / X / Ka. Drives licensing, antenna size and path loss (Chapter 11 §11.5).
2. **Modulation and coding** (Chapter 11 §11.6).
3. **Antenna pattern** — high-gain dish vs patch vs deployable (Chapter 11 §11.3).
4. **Ground-station network** — a single station vs a network (with Ground Segment, Chapter 17).
5. **Link margin allocation** at each phase.

### What you need to know first

- **Daily data volume** from the Payload Lead.
- **Latency requirement** — if any — from the User Representative.
- **Pointing capability** from AOCS in every mode, including safe mode (drives the antenna pattern you can use).
- **Regulatory constraints** for the chosen band (Chapter 2 §2.7; the Compliance Engineer owns the filing).

### Formulas, charts, rules of thumb

- **The link budget** — the canonical equation of Chapter 11 §11.2, $C/N_0 = \text{EIRP} - \text{FSPL} - L_{\text{atm}} - L_{\text{point}} - L_{\text{pol}} - L_{\text{rx}} + G/T - k$, with $k = -228.6$ dBW/K/Hz, and its derivation in Part V §V.7. Keep the polarisation and receive-line losses as separate lines even when they are small; a budget that omits them is the one that fails to close on the pad.
- **Free-space path loss** — Chapter 11 §11.4 and Figure 11.3 (derived in Part V §V.6). Each doubling of range or frequency adds 6 dB. With $R_E = 6378.137$ km, the 10° elevation slant range is 1440 km at 400 km altitude and 1695 km at 500 km; going from nadir to 10° elevation costs 10.6 dB.
- **Modulation and coding** — the BER curves of Figure 11.4 (Part V §V.8); a concatenated code buys about 5 dB at BER 10⁻⁵, LDPC more.
- **Antenna patterns** — Figure 11.2: a dish needs AOCS pointing to a fraction of its beamwidth, a patch tolerates tens of degrees at the cost of 25–30 dB of gain.
- **The waterfall** — Figure 11.5 shows a complete S-band budget read left to right: gains add, losses subtract, the gap to the required $C/N_0$ is the margin.
- **Worked numbers** — Chapter 11 §11.8: the EOSat-3U S-band link closes with 10.4 dB margin at 5 Mbit/s and is bandwidth-limited rather than power-limited; the UniSat-1 UHF link needs forward error correction to meet its 3 dB requirement.

### Common pitfalls

> **Watch out.** Pointing loss is not negligible. For a 1° half-power beamwidth, a 0.3° pointing error costs about 1 dB; at 0.5° it costs about 3 dB.

> **Common mistake.** Forgetting Doppler. A 2.2 GHz S-band link from a 7.5 km/s LEO spacecraft has about ±55 kHz of Doppler at the horizon — the receiver tracking has to follow it.

> **Watch out.** A link that closes is not a data budget that closes. Check Chapter 11 §11.9 — passes per day, usable minutes per pass and protocol efficiency — before telling the Payload Lead the data rate is fine.

### References

- ECSS-E-ST-50-05C — Radio frequency and modulation — [https://ecss.nl/](https://ecss.nl/).
- Pratt, Bostian and Allnutt, *Satellite Communications* (3rd ed.).
- ITU-R Recommendations — [https://www.itu.int/en/ITU-R/](https://www.itu.int/en/ITU-R/).

---

## Propulsion Engineer

You own the Δv. (Even if your CubeSat has none, you decide that.)

### Decisions you own

1. **Need for propulsion** — drag make-up? deorbit? phasing? formation? rendezvous? (Chapter 12 §12.2.)
2. **Propellant choice** — cold gas / monopropellant / bipropellant / electric (Hall, ion, PPT, FEEP).
3. **Thruster sizing** — thrust vs Isp vs power.
4. **Total propellant mass** — the rocket equation.
5. **Plume impingement and contamination plan.**

### What you need to know first

- **Δv budget** — the sum of all required manoeuvres with margin, from the Mission Analyst (Chapter 7 §7.5).
- **Mission duration** — drives cumulative Δv for drag-dominated orbits.
- **Available power** — drives electric-propulsion feasibility (a CubeSat with 20 W cannot run a 200 W Hall thruster).

### Formulas, charts, rules of thumb

- **The rocket equation** — Chapter 12 §12.2.2 and Figure 12.2 (Δv against mass ratio for representative Isp); derived in Part V §V.3. For the ~100 m/s of a CubeSat deorbit burn the curve is nearly linear; for an orbit transfer the exponential takes over.
- **Worked numbers** — the deorbit case of Chapter 12 §12.2.5: 112 m/s from 600 km to a 200 km perigee, with the propellant mass for cold gas, monopropellant and electric options.
- **Debris compliance** — natural lifetime from Chapter 7 §7.3.3 against the rules of §7.3.2; if the natural lifetime does not comply, the deorbit Δv is a requirement, not an option.

### Common pitfalls

> **Watch out.** Isp is a function of inlet conditions and nozzle expansion ratio. Quote the value at the operating point you will actually fly.

> **Common mistake.** Confusing total mass ($m_0$) with dry mass ($m_f$) when applying the rocket equation — and forgetting that the propellant mass changes the structure's mass and the AOCS engineer's inertia tensor.

### References

- Sutton and Biblarz, *Rocket Propulsion Elements* (9th ed.).
- ECSS-E-ST-35C — Propulsion general requirements — [https://ecss.nl/](https://ecss.nl/).
- Goebel and Katz, *Fundamentals of Electric Propulsion*.

---

## Structures Engineer

You make sure the spacecraft survives launch and on orbit, and that everyone else's hardware is mechanically interfaced.

### Decisions you own

1. **Primary structure topology** — monolithic, panel-and-rib, or additively manufactured.
2. **Material selection** — Al, Ti, CFRP, sandwich.
3. **Mass-budget closure with margin** (with the Systems Engineer: Chapter 8 §8.4 and Table 8.3).
4. **Launch-load verification path** — analysis (FEA), test, or both (Chapter 14 §14.3).
5. **Mechanical interfaces** — fastener pattern, deployer compatibility (Chapter 12 §12.1).

### What you need to know first

- **Launcher environment** — qualification levels for sine, random vibration and shock (Chapter 14 §14.3).
- **Component mass and centre of gravity** — every subsystem provides this, and the inertia tensor goes to AOCS.
- **The CubeSat Design Specification envelope** — rails, rail-end contact, deployment switches, centre-of-gravity limits (Chapter 12 §12.1).

### Formulas, charts, rules of thumb

- **Margin of safety** — the canonical definition and worked example are Chapter 12 §12.1.6 (Part V §V.13). For Al 7075-T6 the yield allowable is 503 MPa with a yield factor of safety of 1.25.
- **First natural frequency** — above 100 Hz is the usual CubeSat requirement; the box-beam estimate for a 3U in Chapter 12 §12.1 gives about 330 Hz.
- **Rail loads** — the quasi-static launch load on the rails with $g_0 = 9.80665$ m/s² is worked in Chapter 12 §12.1.
- **Rule of thumb.** Fasteners, adhesives and harness add 5–10 % on top of the structural mass; carry them as a line in the mass budget from the first loop.

### Common pitfalls

> **Watch out.** Forgetting fastener and adhesive mass.

> **Common mistake.** Sizing for static loads and missing the dynamic amplification at resonance under random vibration. Apply a Q-factor (typically 5–10) at the first mode.

> **Watch out.** Every deployable (antenna, panel, boom) is a mechanism, and a mechanism is a single-point failure until the FMECA of Chapter 15 says otherwise.

### References

- ECSS-E-ST-32C — Structures — [https://ecss.nl/](https://ecss.nl/).
- Sarafin, *Spacecraft Structures and Mechanisms*.
- CubeSat Design Specification (CDS) Rev 14 — [https://www.cubesat.org/cds-announcement](https://www.cubesat.org/cds-announcement).
- NASA GSFC-STD-7000 (GEVS).

---

## Cost Engineer

You are the team's reality check.

### Decisions you own

1. **WBS structure** (Chapter 16 §16.2, after NPR 7120.5).
2. **Cost-estimating method** — parametric early, analogy, bottom-up later (Chapter 16 §16.1).
3. **Schedule baseline** — milestones, critical path, float (with the Project Manager).
4. **Risk-adjusted estimates** — how to roll risk into both cost and schedule (Chapter 16 §16.4).

### What you need to know first

- **The bill of materials** from Chapter 13 — equipment costs, lead times and TRL (§13.2 for the TRL risk factor).
- **Non-recurring engineering** — Chapter 13 §13.1.3 gives the NRE build-up; do not restate it in the parametric model.
- **The number of units** — the learning curve of Chapter 16 §16.3 (with the exponent of Chapter 4 §4.6.4) changes the answer for a constellation.
- **The programmatic ceiling** and what the sponsor counts as "cost" (launch, operations, ground segment in or out).

### Formulas, charts, rules of thumb

- **Cost-estimating relationships** and their accuracy by phase — Chapter 16 §16.1.
- **Learning curve** — Chapter 16 §16.3: on a 90 % curve the tenth unit costs 70 % of the first, and twenty units cost 14.6 times the first, not twenty.
- **Cost risk** — the P50/P80 S-curve of Chapter 16 §16.4; report P80, manage to P50.
- **Worked numbers** — the EOSat-3U estimate in Chapter 16 §16.1 and the UniSat-1 roll-up (about 85 kEUR, indicative 2026) in Chapter 13 §13.6 and Chapter 16 §16.4.3.

### Common pitfalls

> **Common mistake.** Treating the parametric tool's output as the answer. The output is a starting point; tailor it for your mission and the launch market you are working in.

> **Watch out.** CubeSat COTS prices date fast and are quoted without integration, test or spares. Mark every price with its year and what it includes.

### References

- NASA NPR 7120.5F — [https://nodis3.gsfc.nasa.gov/](https://nodis3.gsfc.nasa.gov/).
- Wertz et al., *Space Mission Engineering*, Ch. 23 (cost).
- SMAD4 Ch. 20.
- NASA *Cost Estimating Handbook* — [https://www.nasa.gov/cost-estimating-handbook/](https://www.nasa.gov/cost-estimating-handbook/).

---

## Compliance Engineer

You make sure the mission is allowed to fly — by the standards it has adopted, by the regulators who license it, and by the export-control regimes its parts came through.

### Decisions you own

1. **Standards applicability and tailoring.** Which ECSS / NASA standards apply and at what level — the tailoring matrix (Chapter 3 §3.2, after ECSS-S-ST-00-02C).
2. **Frequency licensing strategy.** Amateur (IARU) vs commercial allocation; the ITU advance publication, the national filing and their lead times (Chapter 2 §2.7).
3. **Export-control classification** for every component (ITAR / EAR / Canadian controlled goods), with Procurement (Chapter 2 §2.8, Chapter 13 §13.4).
4. **Debris-mitigation compliance** — 25-year IADC, 5-year FCC where it applies, casualty risk (Chapter 3 §3.6, Chapter 7 §7.3.2).
5. **Remote-sensing licence** under the RSSSA if the mission images the Earth (Chapter 2 §2.6), and registration of the object after launch (Chapter 3 §3.7).

### What you need to know first

- **The orbit and lifetime** from the Mission Analyst — the debris case stands or falls on it.
- **The band, EIRP and ground stations** from Communications — the filing cannot start without them.
- **The bill of materials** from Chapter 13 — origin and classification of every part.
- **Payload resolution and data-distribution plan** from the Payload Lead and User Representative — these decide whether the RSSSA applies and at what level.

### Formulas, charts, rules of thumb

- **The compliance register** — the format of Chapter 3 Table 3.1: standard or regulation, the parameter it depends on, the phase by which it must be closed, the evidence.
- **Licensing timeline** — the lead times of Chapter 2 §2.7.4; spectrum coordination is routinely the longest pole in a CubeSat schedule, and it starts before the design is frozen.
- **Rule of thumb.** Every regulatory filing is a requirement with a verification method (Chapter 14): put it in the verification matrix with a date, not in a memo.

### Common pitfalls

> **Watch out.** Starting the frequency filing after the design is frozen. Coordination takes a year or more; a band change late in Phase B rewrites the link budget, the antenna and the licence.

> **Common mistake.** Assuming a COTS part is export-free because it was bought from a catalogue. Classification follows the part's origin and its technology, not its price.

> **Watch out.** Debris compliance is assessed on the spacecraft as flown — the deployed area, the final mass, the actual altitude — not on the Phase A numbers. Re-run it at every gate.

### References

- ECSS-S-ST-00-02C — Tailoring — [https://ecss.nl/](https://ecss.nl/).
- ISED, *Client Procedures Circular CPC-2-6-02* (licensing of space stations) — [https://ised-isde.canada.ca/](https://ised-isde.canada.ca/).
- *Remote Sensing Space Systems Act* (RSSSA) and regulations — [https://laws-lois.justice.gc.ca/](https://laws-lois.justice.gc.ca/).
- ITU Radio Regulations, Article 9 (coordination) — [https://www.itu.int/pub/R-REG-RR](https://www.itu.int/pub/R-REG-RR).
- IADC Space Debris Mitigation Guidelines — [https://www.iadc-home.org/](https://www.iadc-home.org/).

---

## User Representative

You speak for the people who will use the data. The mission is a success when they say it is, not when the budgets close.

### Decisions you own

1. **Data product requirements** — format, resolution, accuracy, timeliness (with the Payload Lead: Chapter 4 §4.3).
2. **User access methods** — API, portal, direct download (with Ground Segment: Chapter 17 §17.1).
3. **Service levels** — availability, response time, data freshness.
4. **Validation** that the system as designed meets what the stakeholders asked for (Chapter 14 §14.1 — validation is your word, verification is the engineers').
5. **The user's voice in trade studies** — you sit on the trade-study panel of Chapter 4 §4.5 and score the options from the user's side.

### What you need to know first

- **Who the users are** — research, commercial, public, operational — and how they differ (Chapter 4 §4.2).
- **What they do with the data today**, without this mission, so that you can state the need rather than the wish.
- **The downlink and latency the system can actually deliver** (Chapter 11 §11.9, Chapter 17 §17.2), so that the service level you promise is one the mission can keep.

### Formulas, charts, rules of thumb

- **Need → objective → MoE → MoP → TPM** — the hierarchy of Chapter 4 §4.3.3 is your instrument; every data-product requirement should trace up to a measure of effectiveness the user recognises.
- **The WHAT-not-HOW test** of Chapter 4 §4.1.4: if your requirement names an implementation, rewrite it.
- **Rule of thumb.** A "nice to have" that cannot be traded away is a requirement; a requirement that nobody would miss is a nice-to-have. Sort them before the first trade study, not during it.

### Common pitfalls

> **Common mistake.** Not distinguishing between "nice to have" and actual requirements — and letting the engineers guess which is which.

> **Watch out.** Specifying implementation details (a band, a file format, a satellite) instead of user needs (a latency, a coverage, an accuracy).

> **Watch out.** Assuming unlimited bandwidth for data delivery. The daily volume the spacecraft can downlink (Figure 11.6) is the ceiling on what any user can receive, however good the portal.

### References

- NASA SEH §4.1 — Stakeholder expectations definition — [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/).
- ECSS-E-ST-10C §5.2 — Requirements engineering — [https://ecss.nl/](https://ecss.nl/).
- ISO 9241 — Ergonomics of human-system interaction.

---

## Mission Operations Engineer

You will fly the spacecraft after the team builds it — and you rehearse doing so before launch (Chapter 19).

### Decisions you own

1. **Operations concept** — staffing, automation level, shift structure (Chapter 18 §18.1).
2. **Pass plan** — which procedures, in what order, every contact (Chapter 18 §18.4, Chapter 17 §17.4).
3. **Anomaly response tree** — who calls what, when (Chapter 18 §18.5).
4. **Telecommand and telemetry definition** — coordination with the Software Engineer.
5. **LEOP sequence** — first contact, deployments, commissioning timeline (Chapter 19 §19.4).

### What you need to know first

- **The operational modes and their transitions** from the ConOps (Chapter 18 §18.2 and Table 18.1).
- **Ground-station coverage** from the Mission Analyst and Ground Segment (Chapter 17 §17.2).
- **The FDIR architecture** — what the spacecraft will do on its own before you hear about it (Chapter 18 §18.3).
- **The procedure inventory** — LEOP, commissioning, nominal, contingency, emergency.

### Formulas, charts, rules of thumb

- **Contact time per day and data per pass** — Chapter 17 §17.2.3; a high-latitude station sees a SSO spacecraft on most orbits, a mid-latitude one on four to six.
- **The anomaly library** — Chapter 19 §19.5 lists the symptoms, diagnoses and recoveries worth rehearsing (under-voltage, loss of contact, loss of fine pointing, unexpected safe mode, thermal exceedance, mass memory full, command rejected, and the ground fault that looks like a spacecraft fault).
- **Rule of thumb.** The first eight hours after separation are the most critical of the mission; script them to the minute, and rehearse the script.

### Common pitfalls

> **Watch out.** Voice-loop discipline is the silent killer. Cross-talk that sounds harmless in rehearsal breaks down under real-time pressure.

> **Common mistake.** Not planning for degraded operations — a single ground station, a partial deployment, office-hours staffing when the plan assumed 24/7.

> **Watch out.** Seasonal and geometric gaps in station visibility; a station that is fine in the simulation may be unusable at the β-angles of launch season.

### References

- ECSS-E-ST-70C — Ground systems and operations — [https://ecss.nl/](https://ecss.nl/).
- ECSS-E-ST-70-32C — Test and operations procedure language.
- NASA-HDBK-1002 — Fault management handbook; GSFC-STD-1000 — Rules for the design, development, verification and operation of flight systems.

---

## Ground Segment Engineer

You own the architecture between the antenna and the user.

### Decisions you own

1. **Ground-station network** — owned, leased or commercial; a single station or a network (Chapter 17 §17.1, §17.5).
2. **Mission-control software** — open-source or commercial.
3. **Archive and processing design** — L0 → L1 → L2 → distribution, and the latency of each step.
4. **Pass-planning and scheduling tools.**
5. **Cyber-security architecture** — command authentication, link encryption, network segregation.

### What you need to know first

- **Daily data volume** — drives bandwidth contracts and archive growth.
- **Latency requirement** from the User Representative — drives station density.
- **Mission classification** — defence and dual-use missions need different architectures from civil ones.
- **The protocol stack** the spacecraft will speak (Chapter 17 §17.3).

### Formulas, charts, rules of thumb

- **Contact geometry** — Chapter 7 §7.4.1 and Chapter 17 §17.2: the pass profile of Figure 17.2, the maximum pass of 7.4 min at 500 km with a 10° mask, 9.2 min at 5°.
- **Daily capacity** — the station-by-station volumes of Chapter 17 §17.2.3 and the closure against generation in §17.5; the UniSat-1 shortfall with one station is worked in §17.6.
- **Rule of thumb.** Commercial ground-station pricing can flip the economics between bands and between a few long passes and many short ones; do the arithmetic at the data rate you will actually fly.

### Common pitfalls

> **Watch out.** Pricing models for ground-station-as-a-service charge by the minute or by the pass; the cheapest band on paper may not be the cheapest per megabyte.

> **Common mistake.** Designing the ground segment after the space segment is frozen. The station network is part of the link budget (Chapter 11 §11.7) and part of the data budget (§11.9); it belongs in the first design loop.

### References

- CCSDS Mission Operations and cross-support standards — [https://public.ccsds.org/Pubs/](https://public.ccsds.org/Pubs/).
- ECSS-E-ST-70C — Ground systems and operations — [https://ecss.nl/](https://ecss.nl/).
- SMAD4 Ch. 14–15.

---

## Software Engineer (OBDH and flight software)

You own the flight computer, the flight software, the telemetry list and the on-board half of FDIR.

### Decisions you own

1. **OBC architecture** — single board or redundant pair; system-on-chip vs discrete (Chapter 12 §12.3).
2. **Bus topology** — CAN / I²C / SPI / RS-422 / SpaceWire (the interface types of Chapter 8 Table 8.2).
3. **Memory architecture** — RAM, flash, mass memory, EDAC scheme (Chapter 12 §12.3.3 for sizing).
4. **Flight-software architecture** — mode manager, AOCS control loop, TM/TC handler, FDIR rules (Chapter 18 §18.3).
5. **Service set** — which CCSDS/PUS services to implement; the telecommand and telemetry dictionaries.

### What you need to know first

- **TM/TC volume** from each subsystem.
- **Real-time loop rates** required by AOCS.
- **The longest no-contact gap** — sizes the mass memory (Chapter 12 §12.3.3; EOSat-3U uses a three-day outage case).
- **The ground software** it must talk to (Chapter 17 §17.3).

### Formulas, charts, rules of thumb

- **Mass-memory sizing** — longest contact gap × peak data rate × a margin of 1.5–2; Chapter 12 §12.3.3 works the EOSat-3U case.
- **Watchdog timer** — typically 30 s for a CubeSat OBC; shorter for high-criticality threads. Chapter 15 §15.5 carries the OBC watchdog as risk R-03 for UniSat-1.
- **EDAC overhead** — Hamming SECDED costs about 12.5 % for 64-bit words.
- **Rule of thumb.** The I²C-versus-RS-422 interface example of Chapter 8 §8.3 is the shape of most OBDH interface conflicts: the bus is chosen for convenience and discovered to be wrong for noise or distance at integration.

### Common pitfalls

> **Watch out.** Telemetry-list overruns are the number-one late OBDH defect. Lock the list at SRR; treat any addition as a change-control item.

> **Common mistake.** Writing FDIR rules that are not testable on the ground. Every rule in Chapter 18 §18.3 should have a test case in the verification matrix (Chapter 14 §14.4).

### References

- ECSS-E-ST-70-41C — Telemetry and telecommand packet utilisation (PUS) — [https://ecss.nl/](https://ecss.nl/).
- ECSS-E-ST-40C — Software; ECSS-Q-ST-80C — Software product assurance — [https://ecss.nl/](https://ecss.nl/).
- CCSDS 133.0-B — Space Packet Protocol — [https://public.ccsds.org/Pubs/](https://public.ccsds.org/Pubs/).
