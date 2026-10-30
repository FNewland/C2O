# Errata packet EA: facilitator book + learner workbook (Drive course books, EN and FR)

Files: `/home/claude/work/drive_mirror/{,fr/}facilitator_book_expanded.md` (fb) and `{,fr/}learner_workbook_expanded.md` (lw). Every fix is mirrored in FR. mdparity: only the known waivers remain (fb cm³/m² `['1','2','3','3','3']`; lw 5×5 `['5','5','5']`). `tools.i18n accept` was run on both FR files, and both now show in sync. `tools.i18n check` reports 1 error, in `fr/orbit_north_week3.md` [chapter-10-leop-operations]. That file belongs to another packet and was not touched. Internal links: 0 broken in the assembled EN and FR books (FR checked via remap_heading_ids). The French typography count is unchanged from baseline (44 lines).

E1-2.01 | FIXED. Table totals are now 0.91 / 0.67 / 0.50, the same rounding as OER §4.9. The sensitivity check is now 0.76 / 0.72 / 0.73, and the sentence was rewritten: 1U still wins, but 3U overtakes 2U | fb
E1-2.02 | FIXED. 10th-unit costs changed to 84 / 70 / 58 % | fb
E1-2.03 | FIXED. 5 units: 626K / 3,132K. 10 units: 564K / 5,638K | fb
E1-2.04 | FIXED. Iridium weighted scores changed to 4.00 / 4.025 | fb
E1-2.05 | FIXED. Now reads R_system = 4R^3 − 3R^4 | fb
E1-2.06 | NEEDS-FRANZ. The WBS still sums to 103 %. It is kept identical to OER §16.2.1, which awaits Franz's ruling (ERRATA_ED). An earlier unilateral edit (I&T 12→10, Ops 5→4) was reverted in EN and FR | fb (net: none)
E1-2.07 | FIXED. Row 5.0 changed to 39 / 38, totals to ≈91 / ≈91, P80 to ≈118 / ≈118, and the launch share to ~16 %. The BOM-based ≈85 kEUR (Table 4.1.8, follow-on Table 4.4.11) has a different scope (no ops) and was left | fb
E1-2.08 | FIXED. The check now uses EO-Sat-1 at 513 km (orbit.yaml): T = 94.9 min vs 94.5 min (0.4 %), and the residual is explained (a = 6872 km from the mean motion) | fb
E1-2.09 | FIXED. v_p 10.066, ΔV₁ 2.398, v_a 1.618, ΔV₂ 1.457, total 3.854 km/s | fb
E1-2.10 | FIXED. The Fig C.9 caption now gives ≈ −39 °C orbit average (Al ≈ +150 °C, off-scale), consistent with the worked check and cdf fig_thermal_balance.py | fb
E1-2.11 | FIXED. The Fig C.6 caption now matches the rendered cdf figure: 83.4 against 73.0 dB·Hz for 5 Mbit/s, margin +10.4 dB. The stale C.5 cross-check "Figure CO.2 — 162.9 dB" was changed to 164.1 dB (Figure C.6) | fb
E1-2.12 | FIXED. The AC.2 and C.12 captions now say the magnetic dipole dominates at ~1.5 µN·m and give drag as 0.03–0.2 µN·m. "matching" was replaced with a range statement | fb
E1-2.13 | FIXED. Now 0.25 × cosec 5° = 2.87 dB; the gain from 5° to 10° is 4.8 dB, with a 1.5 dB G/T de-rate | fb
E1-2.14 | FIXED. Antenna gains changed to ~34 dBi (S-band) and ~46 dBi (X-band) | fb
E1-2.15 | FIXED. Now 2π(9 mm)²·65 mm ≈ 33 mL | fb
E1-2.16 | FIXED. T₀ = 288 K; the chain was recomputed (14.9 W, 12.4 W, ΔT 30 °C). The conclusion is unchanged | fb
E1-2.23 | FIXED. Verified against ttc.yaml `beacon:` (same conv+RS coding as LOW). The two unstated terms were added: +12.0 dB from the rate (16→1 kbps) and −10.0 dB from the transmit level (10.0 dBW→1 W). The net ~27 dB stands | fb
E1-2.24 | FIXED. Now reads "in about 18 min, so the ~20 min preheat costs … 4.0 Wh" | fb
E1-2.25 | FIXED. Header changed to "Eclipses over the mission duration (15/day)" | fb
E1-2.30 | FIXED. Now ~0.86 MB/day | lw
E1-3.37 | FIXED. Limits changed to 2.00 / 4.00 / 6.0 kg in the 1U text, Table 1.1.14, the alternatives table and MR-002 (×2), and the 2.66 kg waiver was rephrased. The deployer-specific 1.33 kg NanoRacks note (ch 4.1) and the lw NanoRacks margin were kept on purpose | fb
E1-3.38 | FIXED. The thermal equivalent is now GSFC-STD-7000A (GEVS), thermal sections | fb
E1-3.39 | FIXED. The AOCS reference is now ECSS-E-ST-60-30C. The ch 3.2 reference "ECSS-E-ST-60-20C: Star Tracker Performance Testing" was also corrected to the official title and URL, as in OER ch10 | fb
E1-3.40 | FIXED. Hot case uses EOL coatings and cold case uses BOL | fb
E1-3.41 | FIXED. Verified: τ = m×B has no component along B, so roll is uncontrollable at the equator and yaw at the poles | fb
E1-3.42 | FIXED. Verified (SFL mission pages): UniBRITE and BRITE-Austria are Austrian, built by UTIAS/SFL in Toronto; the Canadian pair is BRITE-Toronto and BRITE-Montréal | fb
E1-3.43 | FIXED. Verified (Spaceflight Now / JAXA): the IRU bias was mis-estimated, then wrongly uploaded thruster parameters accelerated the spin | fb
E1-3.77 | FIXED. CDS Rev 14 is now dated 2022 | fb
E1-3.78 | FIXED in part. TAID changed to ATID (ch 1.1). The wrong ECSS claims were corrected: ECSS-E-ST-10-02C lists test, analysis, review of design and inspection, while the NASA set has demonstration instead (L2613, ch 4.2 note and decision-logic note). NEEDS-FRANZ on unifying ATID (ch 2.1) and IADT (ch 4.2) | fb
E1-3.79 | FIXED. The text now says the EO-Sat-1 section uses the flight values (−0.0020/°C, 2.75 %/yr) | fb
E1-3.80 | FIXED. SuperDove bus changed to 6.0–8.4 V | fb
E1-3.81 | FIXED. LDPC gain changed to 6.5–8.5 dB and the green monoprop summary to 230–250 s, both matching the tables | fb
E1-3.82 | FIXED. "Electrodynamic tether" row; "moderate gimbal rate" | fb
E1-3.83 | FIXED. 3U allocation 6000 g, margin 3380 g (56 %), and the Table 4.1.6 caption changed from 6U to 3U. Now "8 line items plus harness" and "6 COTS + 2 custom" | fb
E1-3.84 | FIXED. Equipment-list values were aligned to the BOM (7.5 kEUR, 55 g, 25 g / 2.5 kEUR); totals are unchanged. Downlink is now "4800 bps useful (9600 bps channel)", and storage is based on 1.13 MB/day (~3.5 days) | fb
E1-3.85 | NEEDS-FRANZ. Which sine profile (1.25 g vs the 3.22 g crossover), which single random profile, and proto-flight TVAC limits? The same question is open for the OER (ED) | none
E1-3.86 | FIXED. Now "~30° pointing error" | fb
E1-3.98 | FIXED. Deployment switches: "Minimum 1 (on a rail standoff)" and "Min 1" (checklist was already Min 1). The tree now says "PROPULSION LIKELY REQUIRED". The gate uses the FCC 5-year rule | lw
E1-4.03 | FIXED. Ch 1.4 captions realigned (1.4.7–1.4.22) and the summary captioned 1.4.23. Caption 2.1.13 moved onto its verification table; the summary is now captioned 2.1.14 | fb
E1-4.04 | FIXED. Ch 2.4: 2.4.6–2.4.13 realigned and the summary captioned 2.4.14. Ch 2.3: 2.3.8 moved onto the UniSat-1 orbit-fit table, the summary is 2.3.9, and Figure 2.3.2 became 2.3.1 | fb
E1-4.05 | FIXED. Ch 3.2 propulsion captions renumbered 3.2.14–3.2.17 (the 3.4.10 propulsion-trade caption was brought in from ch 3.4) and the summary is 3.2.18. Figure 3.4.1 became 3.2.2 | fb
E1-4.06 | FIXED. Ch 3.4: FoS 3.4.6 (moved from ch 3.2), processors 3.4.7 through FSW functions 3.4.10, summary 3.4.11. Ch 4.1: 4.1.4–4.1.14 realigned, Iridium 4.1.15, budget fixes 4.1.16, summary 4.1.17. Ch 4.4: 4.4.6–4.4.14 realigned, summary 4.4.15. All 229 captions are now sequential, with the same structure in EN and FR | fb
E1-4.07 | FIXED in part. The PCDU/EPS figure was moved under "EPS Block Diagram". LEFT (book-wide convention): numbering the many unnumbered figures | fb
E1-4.08 | FIXED. The xmlns attribute was repaired in all 8 SVGs (EN and FR); the lw has no inline SVG | fb
E1-4.09 | FIXED. The ch 3.4 propulsion objectives 5–6 were removed and the rest renumbered 5–7. The reading list was kept | fb
E1-4.10 | FIXED. "Figure 1.1.3" now reads "the System-V figure in Chapter 1.1", and "Figure 4.3.2" now reads "the risk matrix above" | fb
E1-4.11 | FIXED. The N² duplicate entries were merged, and the "Structure & on-board data handling (ch.)" entry was relabelled. Five anchors were repointed (AOCS/TT&C func_id ranges, S12 ×2, S19). 0 broken links in EN and FR | fb
E1-4.18 | LEFT. Not specific to ch 2.1: chapters 2.1–3.4 all put References before Learning Objectives. Reordering eight chapters is a structural change | none
E1-4.19 | FIXED. 4 grammar fixes (FR was already correct) | fb
E1-4.20 | FIXED. CSA 1990 row moved before RADARSAT-1 | fb
E1-4.21 | FIXED. "Wertz et al.;". The 8 SMAD links now point to microcosminc.com (the publisher, as in the OER). Now "Technical Assistance Agreement (TAA)" | fb
E1-4.22 | FIXED. "the power budget closes"; "comparable eclipse"; the payload row gets its 5th cell. The 3U inertia remark now uses the 5 kg 3U (3.3 °C, consistent with the transient below it) | fb
E1-4.23 | FIXED in part. The garbled capacity sentence was rewritten and "my approximation" removed. LEFT: "kbps" (used 22 times in the book; a units sweep is a style decision) | fb
E1-4.24 | FIXED within this book. 7 "EOSAT-1" changed to "EO-Sat-1", the book's majority spelling; the `eosat1` paths are untouched. NEEDS-FRANZ on the canonical spelling across documents | fb
E1-4.46 | FIXED in part. The V&V sentence was corrected. The UHF required-Eb/N0 row now reads "GMSK + conv. code r=1/2 (K=7)", 5.0 dB, as in the facilitator book's Remedy 1. LEFT: DOD/DoD (the workbook uses DOD consistently) | lw
EXTRA Gateway/Canadarm3 | FIXED. The 5 replacements recommended in ERRATA_ED / GATEWAY_STATUS were applied to the Table 1.2.1 caption, its Canadarm3 and Gateway rows, the focus-area row and the partnerships row. FR uses the OER's « suspension » wording | fb
EXTRA footer-fr | FIXED. Now « Manuel du cours SpaceCDF · 2026 » in the EN and FR front matter | fb
EXTRA index anchors | FIXED (see E1-4.11) | fb
EXTRA FR SVG labels | FIXED. All 8 FR SVGs carry French labels; ids, coordinates and attributes are identical to EN. Checked for overflow with font metrics: one label was shortened (« Tests unit. »), and « Centre de contrôle » now follows the glossary. The SVG universal-function IDs F-011…F-014 were changed to F-020…F-050 (EN and FR) to match the book's own function tree, the workbook and the OER (E1-3.90). The lw has no inline SVG | fb

## Needs Franz
1. WBS 103 % (E1-2.06): which Level-1 share should be cut? The facilitator book stays identical to OER §16.2.1. ED recommends cutting Bus from 30 % to 27 %.
2. Should one acronym be used book-wide (ATID in ch 2.1, IADT in ch 4.2)? Renaming the ch 4.2 headings changes their anchors (E1-3.78).
3. Vibration profiles (E1-3.85): which sine profile (1.25 g vs the 3.22 g crossover), which single random profile, and proto-flight TVAC at qualification levels?
4. Canonical spacecraft spelling across all documents: EO-Sat-1 or EOSAT-1 (E1-4.24)?

## Tests
This packet touched no smo files and no procedures. The pytest run (tests/test_content and tests/test_i18n) gave 10 failed and 2068 passed. Compared with the earlier session baseline, the generated_command_reference failures are gone. Two new ids, CTG-002 command_services and test_i18n_check_has_no_errors, come from procedure edits made in parallel by other packets; this packet caused none of them. The generated files (smdl, xtce, PARAMETER_MAP) were restored afterwards.
