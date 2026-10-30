# OER proof-read — `Concurrent_Spacecraft_Design_OER.pdf`

Independent proof-read of the built PDF (367 pages after fixes; was 370). Method: every page rendered with pymupdf at 60 dpi and 70+ pages viewed as contact sheets; full text extracted and swept with the spec §7 regex and the extra list; cross-reference index built from `chapters/*.md`; eight numbers recomputed from scratch; twelve captions checked against their images; licence pages read.

## 1. Pages sampled (final build numbering)

| Set | Pages |
|---|---|
| Cover / TOC / preface | 1, 2, 3, 4, 5, 6, 7, 8 |
| Part openers | 9, 123, 228, 325, 326, 346, 347 |
| Chapter openers (all 19) | 10, 27, 41, 56, 74, 85, 93, 108, 124, 150, 175, 200, 229, 243, 256, 268, 284, 296, 310 |
| Random body | 36, 41, 49, 60, 89/90, 121, 177, 199, 214/215, 271/272, 286/287, 310/311 |
| New-figure pages (all 21) | 32, 36, 61, 69, 77, 103, 135/136, 151, 161, 201/202, 210, 231/234, 250, 266/267, 273, 277, 274/280, 285/289, 295, 297/303, 305 |
| Inline-SVG figure pages | 18, 42/43, 62, 86, 94, 109, 110, 125, 177 |
| Other figures | 13, 16, 96, 100, 117, 193, 353 |
| Table-heavy | 183, 212/213, 236, 249, 259/260, 214/215 |
| Problems | 71, 148, 266 (+ all 19 Problems pages text-swept) |
| Back matter | 362, 364, 365, 366, 367 |

## 2. Defects found

| # | Page(s) (orig. build) | Defect | Fixed? |
|---|---|---|---|
| 1 | every `°` inside math (46 occurrences; e.g. 96, 100, 103, 161) | Degree sign in mathtext rendered as an **"fl" ligature** ("68.0fl", "i = 97.79fl"): Computer Modern has no U+00B0. | **y** — `docs/_render_math.py` maps `°` → `^\circ` before rendering |
| 2 | 32, 73, 198 | Currency dollars parsed as inline math: "~$2B … $150B+ programme" rendered as a formula "150B + programme, yielding", leaving a bare "L \approx 75$" in prose; same in Ch 4 Problem 7 ("$4M") and Ch 11 Problem 9 ("$500 per pass"). | **y** — escaped as `\$` in the three chapter sources; renderer now unescapes `\$` after math substitution |
| 3 | 2–5 | TOC section entries (level 2) had leader dots but **no page numbers** — `build_toc` slugs ("1-1-what…") did not match Python-Markdown's ids ("11-what…"). | **y** — `build_oer.py` now uses `markdown.extensions.toc.slugify` |
| 4 | 43, 235, 304 | Captions of Figures 3.1, 13.2, 18.1 orphaned at the top of the page after their image. | **y** — `img`, `.inline-svg { page-break-after: avoid }` |
| 5 | 185–186, 215–216, 240–241, 253, 264–265 | Five wide tables (band comparison, processor table, UniSat-1 BOM, VCRM, FMECA) **ran off the right page edge** (text to x ≈ 600 pt on a 595 pt page). | **y** — tables with ≥ 8 / ≥ 10 columns get class `wide`/`xwide` (smaller font, in-word breaking allowed); body cells `overflow-wrap: break-word`. No block now exceeds the text column. |
| 6 | 89, 138, 141, 171, 193–194 and 25 other places | **Lists following a paragraph line inside worked-example boxes rendered as run-on prose** ("where: - P = …"), and the Ch 6 function-tree fenced block inside a blockquote showed literal ``` with the tree collapsed. 11 nested lists (3-space indent) also collapsed. | **y** — `build_oer.py` `_normalise_lists()`: blank line before such lists, 4-space nested indent, blockquoted fences → indented code |
| 7 | 96, 102–104, 287 etc. | Justified worked-example paragraphs with inline-math images produced very wide word gaps. | **y** — `blockquote p { text-align: left }` |
| 8 | 56, 69, 108, 117 … | Long chapter titles made the running header wrap and pushed "Concurrent Spacecraft Design" onto two lines. | **y** — explicit widths (26 % / 72 %), 8 pt |
| 9 | 329 | Part IV title page continued straight into body text with an orphaned "Systems Engineer" heading at the foot. | **y** — `h1.part { page-break-after: always }` (Parts I–III unchanged; no blank pages introduced) |
| 10 | 7–8 | Preface pages carried running header "Contents" because "How to use this book" was an h2. | **y** — promoted to h1 (now also listed in TOC) |
| 11 | 357, 359 | Part V §V.6/§V.7 "Verification" described the **old** Figure 11.5 (2.2 GHz, 1500 km, 3.7 m dish, C/N₀ 113.6 dBHz vs 50 dBHz) while the figure/caption show the §11.8.1 case (2.25 GHz, 1695 km, 3 m, 83.4 vs 73.0 dBHz); Ch 11 §11.8.1 also said the figure was "a closely related case". | **y** — three sentences corrected to the figure as drawn |
| 12 | 365 | Appendix A: "available at `<repository URL>`" placeholder. | n — author must supply |
| 13 | 289 | Figure 17.1: "Conjunction assessment" text spills out of the Flight-dynamics box. | n — figure script |
| 14 | 94 | Figure 7.1 (inline SVG, orbit elements): large blank area, inclination shown as a dashed line rather than an angle; FIGURE_QA already asked for a redraw. | n |
| 15 | 369 | Acknowledgement says "The AIG logo is used under its own licence terms" but no logo is placed in the book. | n — add the logo or drop the sentence |
| 16 | 136 | Figure 9.5 hot-case box lists "Earth IR 200 W/m²" while the Earth label says "q_IR = 240 W/m²" (caption makes no numeric claim). | n |
| 17 | 212 vs 210 | §12.2.5 table uses 5 kg *initial* mass (0.87 kg cold-gas for 100 m/s) while the Figure 12.3 stars/worked example use 5 kg *dry* mass (1.05 kg for 112 m/s). Both internally correct; convention differs. | n |

Text sweep after rebuild: spec §7 regex = 0 hits in PDF text and sources; `FIGURE-TODO|TAID|ATID|IADT|\?V|Ã|â€|Course Plan|{: .part|SVG_PLACEHOLDER|../../assets` = 0; "the the"/doubled words = 0 (table-cell adjacencies only); no "students/participants/instructor/SpaceCDF" inside any Problems section; no empty pages; no caption separated from its figure; no text block beyond the text column.

Cross-references: index of 471 numbered headings, 59 figure captions, 12 table captions built from the sources. Every `§N.x`, `Figure N.x`, `Table N.x`, `Chapter N` reference resolves; the only non-matches are citations of external documents (SMAD4 Ch. 20/29, NASA SEH §6.8, INCOSE §2.3.5, ECSS §5.4.2.3).

## 3. Numerical spot-check (recomputed with μ = 398 600.44 km³/s², R_E = 6378.137 km)

| Quantity | Book | Recomputed | OK |
|---|---|---|---|
| 450 km circular period | 93.6 min (Part IV) | 5615.2 s = 93.59 min | y |
| 500 km / 10° slant range | 1695 km | 1695.1 km | y |
| FSPL, 2.25 GHz, 1695 km | 164.1 dB | 164.07 dB (exact), 164.08 (92.45 form) | y |
| Eclipse fraction, β = 0, 500 km | 0.378 → 35.8 min of 94.6 | 0.3779 → 35.8 min of 94.6 | y |
| EOSat-3U array area (Ch 9 chain) | 13.82 W EOL → 16.0 W BOL → 0.0526 m² | 13.82 → 16.04 → 0.0526 m² | y |
| Learning curve, L = 0.9, 10th unit / 10-unit cumulative | 70 % / 8.00 | 0.7047 / 7.994 | y |
| 3-of-4 wheels, R = 0.98 (and 3 series) | 0.9977 ≈ 0.998 (0.941) | 0.99766 (0.9412) | y |
| UniSat-1 UHF C/N₀ (Ch 11 §11.8.2) | 55.1 dBHz, E_b/N₀ 15.3 dB, margin +2.8 dB | FSPL 148.43, T 27.78 dBK, C/N₀ 55.10, R_b 39.82 → 15.3 dB → +2.8 dB | y |
| (extra) 400 km / 10° slant range | 1440 km | 1439.6 km | y |
| (extra) Fig 16.3 P80/P50, reserve | 1.07, 31 kEUR | 491/459 = 1.070, 32 (31.2 unrounded) | y |

## 4. Figure / caption agreement

| Figure | New? | Caption claims vs image | Verdict |
|---|---|---|---|
| 2.3 licensing timeline | new | PDR m9, CDR m18, launch m30; hatched critical path; ITU 2–7 yr | match |
| 4.4 data pipeline | new | three segment groups, sizing parameter under each stage, sustainability condition | match |
| 7.2 β / eclipse | — | ISS ±75° envelope; fully sunlit beyond ≈70° (400 km) / ≈66° (600 km); max ≈37 % | match (37.8 % at 500 km recomputed; 400 km → 39 %, plot shows 39 at 400) |
| 7.5 TID vs altitude | new | 1/2/4 mm curves, grey table bars, halving shielding ≈ ×2–3 | match |
| 10.2 wheel pyramid | new | β = 30°, 4 axes 90° apart, 2 cos β / 4 sin β | match (and physically right) |
| 11.5 link waterfall | regen | 2 W, 6 dBi, 2.25 GHz, 1695 km, 3 m/150 K, 83.4 vs 73.0 dBHz, 10.4 dB | match (Part V text corrected to it) |
| 12.3 Isp–thrust map | new | three stars for 112 m/s at 5 kg: 1.05 / 0.249 / 0.048 kg | match; recomputed 1.048 / 0.249 / 0.0478 kg |
| 15.2 RBDs | new | 0.98³ = 0.941; 0.98⁴ + 4·0.98³·0.02 = 0.9977 | match |
| 16.1 cost funnel | new | ±50 % at MCR → ±10 % at CDR, gates marked | match |
| 16.3 S-curve | new | P50 459, P70 479, P80 491, CBE 456.8 ≈ P47 | match |
| 17.3 ops Gantt | new | 24/7 LEOP → 16/7 commissioning → 8/5; weeks axis | match |
| 18.1 state machine | new | Detumble→Nominal; Imaging/Downlink/Eclipse excursions; Safe exits by ground command or rate-limit→Detumble | match |
| D.3 GSD | — | 0.135 m at 786 km → 3.9 m; 90 mm at 500 km → 3.7 m | match (recomputed 3.90 / 3.73 m) |

## 5. Licence / attribution

Cover: "Licensed under Creative Commons Attribution 4.0 International (CC BY 4.0)" with share/adapt sentence and URL. Licence page (p. 365): CC BY 4.0, attribution line "Concurrent Spacecraft Design: An Open Textbook, Franz Newland et al., CC BY 4.0", share/adapt/no-additional-restrictions terms, third-party-material note. The only NC-SA mention is correctly scoped to the AIG logo (Peters 2023), explicitly separated from the book's own licence. Acknowledgement of generative AI page present (p. 366). Every page footer: "CC BY 4.0". No institutional branding anywhere.

## 6. Residual issues for the author

1. Replace `<repository URL>` in Appendix A (p. 362).
2. Either place the AIG logo on the acknowledgement page or delete the "AIG logo is used…" sentence (p. 366 and Licence p. 365 third-party note).
3. Figure 17.1: shorten/enlarge the Flight-dynamics box ("Conjunction assessment" overflows).
4. Figure 7.1 inline SVG: redraw per FIGURE_QA (inclination as an angle; trim whitespace).
5. Figure 9.5: reconcile Earth-IR 200 vs 240 W/m² inside the drawing.
6. §12.2.5 table vs Figure 12.3 / worked example: state whether the 5 kg is dry or initial mass (numbers differ by ~20 %).
7. Cosmetic: 9–10-column tables (VCRM p. 249, FMECA p. 260, BOM p. 236) now fit but break a few words ("Syste-m", "EAR9-9"); a narrower column set or landscape table would read better.
8. "Unit cost (EUR/kEUR)" is used throughout the BOM/cost chapters of a Canadian-context book; confirm the currency choice is intentional.

## 7. Verdict

**Pass with minor residuals.** The eleven defects that affected correctness or readability (broken degree signs in every angle formula, currency-as-math corruption, TOC without section page numbers, five tables cut at the page edge, ~40 run-on lists in worked examples, orphaned captions, and a Part V verification paragraph describing a figure that no longer exists) are fixed in the sources/build and verified in the rebuilt PDF. All recomputed numbers agree with the book; all cross-references resolve; licence pages are correct. Remaining items are author decisions or figure-script tweaks, none blocking release.
