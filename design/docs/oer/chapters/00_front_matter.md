---
title: "Concurrent Spacecraft Design — An Open Textbook on Mission Design and Concurrent Engineering"
subtitle: "From mission need to operations, with worked CubeSat examples"
authors: "Franz Newland and contributors"
version: "OER edition 1.0 — 2026"
licence: "CC BY 4.0"
language: en
toc: true
---

# How to use this book

This is an open textbook on the design of small spacecraft by the concurrent-engineering method — the way a Concurrent Design Facility (CDF) takes a mission from a stated need to a reviewed baseline, with every subsystem sized in the same room, from the same shared design state, at the same time. It is written for final-year undergraduates, graduate students and early-career engineers who have an engineering background but have not yet designed a spacecraft, and for anyone who wants to understand how the pieces of a mission — orbit, power, attitude, communications, structure, operations, cost, regulation — constrain one another.

The book is organised in five parts, one appendix and a short back matter. Parts I–III are the main text, nineteen chapters that follow a mission from need to operations; Parts IV and V are reference material to be dipped into.

**Part I — Foundations and Design (Chapters 1–8)** lays the foundations: the concurrent-design method and the systems-engineering framework it sits inside (Chapter 1), the regulatory and industrial environment of a Canadian mission (Chapter 2), the international standards a project must apply (Chapter 3), mission needs, stakeholders, trade studies and the concept of operations (Chapter 4), requirements (Chapter 5), functional decomposition (Chapter 6), orbit selection and the space environment (Chapter 7), and the mission architecture with its segments, interfaces and engineering budgets (Chapter 8).

**Part II — Subsystem Design (Chapters 9–12)** sizes the subsystems — power and thermal (Chapter 9), attitude and orbit control (Chapter 10), communications and link budgets (Chapter 11), and structures, propulsion and on-board data handling (Chapter 12).

**Part III — Integration, Verification and Operations (Chapters 13–19)** takes the design through equipment selection and the bill of materials (Chapter 13), verification and validation (Chapter 14), risk, interface control and FMECA (Chapter 15), cost estimation and design reviews (Chapter 16), the ground segment (Chapter 17), mission operations and FDIR (Chapter 18), and finally the rehearsal of a mission before launch (Chapter 19).

Every chapter of Parts I–III follows the same pattern: a short list of recommended background reading, learning objectives, numbered sections, a summary, a set of problems and a reference list. The problems mix conceptual questions, calculations and small design tasks; most can be done with a calculator or a spreadsheet, and a few invite you to use a concurrent-design tool of your choice.

**Part IV — Engineering Position Reference** is a briefing for each of the sixteen engineering positions that sit around a CDF table: what decisions that position owns, what it needs to know from the others before it can decide, the equations and rules of thumb it uses (cross-referenced to Parts I–III rather than restated), the pitfalls that catch first-time designers, and where to read more. Read the briefing for the position you are about to take, and skim one adjacent to it.

**Part V — First-Principles Derivations** derives, from first principles, the equations that the chapters apply — Kepler's third law, the rocket equation, J₂ nodal regression, the eclipse fraction, free-space path loss and the link-budget algebra, bit-error-rate curves, ground sample distance, radiative equilibrium, solar-array and battery sizing, margin of safety, disturbance torques and the daily data-volume closure — each with a worked sanity check against a published value. Use it when you want to know *why* a formula has the form it has, or when a reviewer asks you to show your working.

**Appendix A** describes the open-source concurrent-design tool, SpaceCDF, with which the numerical examples in this book were computed. **The back matter** holds a note on how the book was produced, its licence, an acknowledgement of the generative-AI assistance used in preparing it, and a colophon.

### The two running examples

Two spacecraft recur throughout the book so that the chapters can build on one another's numbers.

- **EOSat-3U** is a 3U Earth-observation CubeSat in a 500 km Sun-synchronous orbit, carrying a multispectral imager and an S-band downlink, with three-axis attitude control. It is the primary worked example of the subsystem chapters (power, attitude, communications, structure) and of the budget, verification, risk, cost and operations chapters that follow. Where a chapter says "the 3U EO CubeSat", this is the spacecraft meant.
- **UniSat-1** is a 1U technology demonstrator carrying a MEMS magnetometer, with passive magnetic stabilisation, a UHF link and no propulsion. It is introduced in Chapter 1 §1.7 as the deliberately simpler second example; each later chapter closes with a short "Returning to UniSat-1" section that applies the chapter's method to it. Because UniSat-1 is small enough to hold in your head, it is a good vehicle for the end-of-chapter problems.

The two are never interchangeable: numbers quoted for the 3U EO CubeSat are not UniSat-1 numbers, and vice versa.

### Recommended background reading

The book assumes an engineering background — mechanics, basic electromagnetism, elementary thermodynamics and the calculus that goes with them — but no prior spacecraft design. The following references are cited throughout and are worth having to hand:

- NASA, *Systems Engineering Handbook* (SP-2016-6105 Rev 2), §1–§3 for the systems-engineering framework. [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/)
- NASA, *NPR 7123.1D — Systems Engineering Processes and Requirements*, §3. [https://nodis3.gsfc.nasa.gov/](https://nodis3.gsfc.nasa.gov/)
- NASA, *CubeSat 101: Basic Concepts and Processes for First-Time CubeSat Developers*. [https://www.nasa.gov/wp-content/uploads/2017/03/nasa_csli_cubesat_101_508.pdf](https://www.nasa.gov/wp-content/uploads/2017/03/nasa_csli_cubesat_101_508.pdf)
- Wertz, Everett and Puschell (eds), *Space Mission Engineering: The New SMAD*, Microcosm Press, 2011 — cited as "SMAD4" throughout.
- ECSS, the European Cooperation for Space Standardization standards, in particular ECSS-E-ST-10C (system engineering), ECSS-M-ST-10C (project planning) and ECSS-E-ST-10-02C (verification). [https://ecss.nl/](https://ecss.nl/)
- Vallado, *Fundamentals of Astrodynamics and Applications*, 4th edition, for the orbital mechanics of Chapter 7 and Part V.

Each chapter opens with a shorter, topic-specific list.

### How the numerical examples were produced

Every numerical worked example in this book — the EOSat-3U and UniSat-1 budgets, the orbit timings, the link-budget closures, the thermal cases, the cost roll-ups — was computed with the open-source SpaceCDF tool described in Appendix A, from mission descriptors that are published with the tool, and then checked by hand against the equations given in the text and derived in Part V. The figures are generated procedurally by scripts kept alongside the book's sources, so that a figure can be regenerated when a number changes. Where this edition's editors found and corrected an arithmetic slip in an earlier version, the corrected value is used consistently in every chapter that quotes it. Readers who wish to reproduce or extend an example will find the details in the back matter.

### Conventions

The book uses SI units, UK spelling, and the constants $R_E = 6378.137$ km, $\mu = 398\,600.44$ km³/s², $J_2 = 1.0826 \times 10^{-3}$, $g_0 = 9.80665$ m/s² and $k = -228.6$ dBW/K/Hz throughout (Part V, V.1 lists the full set with sources). Verification methods are abbreviated ATIR(D) — Analysis, Test, Inspection, Review of design, and Demonstration where it is used. Vendor products named in worked examples are representative examples, not endorsements, and any prices quoted are indicative for 2026.
