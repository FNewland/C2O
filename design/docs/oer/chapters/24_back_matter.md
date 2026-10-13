# About this book

*Concurrent Spacecraft Design* is an open textbook on the design of small spacecraft by the concurrent-engineering method. It takes a mission from a stated need, through requirements, orbit selection, architecture and subsystem sizing, to verification, cost, design review, the ground segment and operations, with two running CubeSat examples — a 3U Earth-observation spacecraft (EOSat-3U) and a 1U magnetometer demonstrator (UniSat-1) — carried through every chapter. Part IV briefs each engineering position at a concurrent-design table; Part V derives the equations from first principles.

It is written for final-year undergraduates, graduate students and early-career engineers with an engineering background but no prior spacecraft design experience, and for practising engineers who want a compact, standards-referenced account of how the pieces of a mission constrain one another. Each chapter has learning objectives, a summary, problems and references; the problems need no software beyond a calculator or spreadsheet.

**Reproducible figures.** Every plotted figure in this book is generated procedurally by a short script kept alongside the book's sources, from a reproducible numerical input. There are no hand-drawn plots: a figure can be regenerated when the underlying numbers change, and a reader who wants to see how a curve was computed can read the script that drew it. Schematic diagrams are drawn as vector graphics in the sources.

**Tool-computed examples.** Every numerical worked example — the EOSat-3U and UniSat-1 budgets, the orbit timings, the link closures, the thermal cases, the cost roll-ups — was computed with the open-source SpaceCDF tool described in Appendix A, from mission descriptors published with it, and then checked by hand against the equations in the text and derived in Part V. Where the editors of this edition found an arithmetic slip in an earlier version, the corrected value is used consistently in every chapter that quotes it, and the derivation in Part V shows the corrected working. Readers who want to reproduce an example can run the published descriptor; readers who want to challenge one can follow the derivation.

**Standards.** ECSS standards, NASA handbooks and the SMAD texts are cited at the point of use. Where a standard's wording and common practice differ — the verification methods of Chapter 14 are an example — the book says which is which.

**Corrections and contributions.** This is a living document. Corrections, improved problems and new figures are welcome through the repository given in Appendix A; contributors are acknowledged in the next edition.

---

# Licence

*Concurrent Spacecraft Design: An Open Textbook*, Franz Newland et al., is licensed under the Creative Commons Attribution 4.0 International Licence (CC BY 4.0).

**Attribution.** When reusing or adapting this work, please attribute it as:

> *Concurrent Spacecraft Design: An Open Textbook*, Franz Newland et al., CC BY 4.0.

**You are free to:**

- **Share** — copy and redistribute the material in any medium or format;
- **Adapt** — remix, transform, and build upon the material for any purpose, even commercially.

The licensor cannot revoke these freedoms as long as you follow the licence terms.

**Under the following terms:**

- **Attribution** — You must give appropriate credit, provide a link to the licence, and indicate if changes were made. You may do so in any reasonable manner, but not in any way that suggests the licensor endorses you or your use.
- **No additional restrictions** — You may not apply legal terms or technological measures that legally restrict others from doing anything the licence permits.

You do not have to comply with the licence for elements of the material in the public domain or where your use is permitted by an applicable exception or limitation. No warranties are given. The licence may not give you all of the permissions necessary for your intended use; for example, other rights such as publicity, privacy, or moral rights may limit how you use the material.

The full licence text is at [https://creativecommons.org/licenses/by/4.0/](https://creativecommons.org/licenses/by/4.0/).

**Third-party material.** Standards, handbooks and papers quoted or summarised in this book remain the property of their publishers and are cited at the point of use. Vendor products named in worked examples are representative examples, not endorsements, and their trademarks belong to their owners. The AIG (Assisted by Generative AI) logo used in the acknowledgement below is published under its own CC BY-NC-SA 4.0 terms, which govern its reuse separately from the CC BY 4.0 licence of this book.

---

# Acknowledgement of generative AI

This book was produced with the assistance of generative AI. The structure of the chapters, the conversion of earlier material into textbook prose, the drafting of problems, the figure-generation scripts and the document rendering were prepared with AI assistance, guided throughout by the ECSS standards, the NASA Systems Engineering Handbook and the SMAD references cited in the text. The numerical examples were computed by the SpaceCDF tool (Appendix A) and checked by hand. Editorial framing, the worked examples, the selection of what to include and omit, and responsibility for every claim in the book remain with the human authors.

Attribution follows the AIG (Assisted by Generative AI) framework — Peters (2023), *Logos IA-EN*, CC BY-NC-SA 4.0 — [https://mpeters.uqo.ca/en/logos-ia-en-peters-2023/](https://mpeters.uqo.ca/en/logos-ia-en-peters-2023/). The AIG logo is used under its own licence terms, which differ from the licence of this book (see the Licence page above).

Readers who adapt this book are encouraged to keep the same practice: say where generative AI was used and how. Declining to use AI is fine; using it without saying so is not.

---

# Colophon

The book is written in Markdown, one file per chapter, with mathematics in LaTeX notation; the plotted figures are generated by matplotlib scripts kept with the sources, and the schematic diagrams are inline SVG. The chapters are concatenated in order, converted to HTML, and rendered to PDF by WeasyPrint. Fonts are the renderer's default sans-serif and serif families; the accent colour used in figures and headings is a neutral blue.
