# Open questions for Franz (2026-10-28, after the errata pass)

Everything else in `ENGLISH_ERRATA.md` has been fixed in both English and French. These items need an author's ruling. Each one names its errata ID, so the packet reports in `docs/i18n/errata_reports/` give the detail.

## A. Mission and spacecraft facts (one answer fixes many documents)

1. **Orbit altitude.** `orbit.yaml` is 513 km, but the ops book and parts of the manual compute everything at 450 km (GSD 29.3 m, swath 240 km). Should the books move to 513 km (GSD 33.4 m, swath 273 km)? *(E1-3.48, NEW-2)*
2. **Dawn–dusk or not?** The TLE gives LTAN ≈ 10:00 and β between −13° and −43°. The manual chapters 00 and 07 say 06:00/18:00 dawn–dusk. *(E1-3.49)*
3. **Orbital decay and deorbit capability at 513 km.** Re-deriving it may overturn the "no deorbit capability" ruling. The manual's ballistic coefficient (~200 kg/m², >7 years) disagrees with `prop.yaml` (77.9 kg/m², 1.7–4.8 years). *(E1-3.97, NEW-2)*
4. **Body frame.** `eps.yaml` puts the imager and radiator on −Z; manual chapters 00, 02 and 06 put the payload on +Z (nadir). *(E1-3.10)*
5. **OBC mode model.** The manual uses mode 2 = BOOTLOADER. In the tree, 2 = emergency, and the bootloader shows as `sw_image` = 0. Should the manual switch to `sw_image`? *(NEW-1)*
6. **AOCS mode labels.** `tc_catalog` says NOMINAL_NADIR / ECLIPSE_PROPAGATE for modes 4/8; `aocs_mode_codes.yaml` says NOMINAL / ECLIPSE. Which is canonical? *(E1-3.19)*
7. **Transponder auto-switch.** 120 s (manual 05) or 24 h (manual 08)? The RSSI thresholds (−105 or −100 dBm) exist in no config. *(E1-3.27)*
8. **Spelling.** EO-Sat-1 or EOSAT-1, across all documents? *(E1-4.24)*

## B. Procedures (the runner sends whatever is written)

9. **CTG-025:** if ST2 doesn't track, go to Off-Nominal (L98) or to Step 5 (L110)? And how does Step 5 choose among modes 4, 3 and 2?
10. **EMG-001 Step 3:** in DETUMBLE before rates are below 0.1 °/s, wait (with what timeout) or continue? Should "return to Step 7" be a bounded loop?
11. **CTG-010:** should the fork into Step 6 test `obdh.mode == 1`? Which clock-drift threshold applies: 1 s, 2 s or 5 s? *(E1-3.31)*
12. **`obdh.task_shed`** (CTG-004, CTG-010) doesn't exist. What OBC-load reduction is intended?
13. **CTG-004** escalates a thermal red limit to EMG-002 (Total Power Failure). Should that be EMG-006 (Thermal Runaway)?
14. **CTG-008:** after an AOCS safe-mode trigger it sends you to CTG-005 (EPS Safe Mode Recovery). Should that be CTG-002?
15. **Bootloader cards:** CTG-018 or CTG-021 is canonical. *(E1-1.79)*
16. **COM-003** needs a ruling on tracker-in-COARSE_SUN versus the Step 4 precondition, the "300 s of NOMINAL", the 0.10 °/s gate with wheels off, and its "Revision 2.0" heading. *(E1-3.53)*
17. **LEOP bands:** LEOP-003 altitude [400, 550] or [495, 540] km? LEOP-004 bus [27.0, 29.5] or [26.0, 30.0] V? *(E1-3.54)*
18. **EMG-002 survival load:** the table sums to 45 W, but Steps 5 and 6 use 32 W. *(E1-3.56)*
19. **NOM software upload:** is "previous image retained in alternate bank" true? *(E1-3.61)*
20. **COM-007** reads 0x0304/0x0305 as EDAC count and watchdog status, but they are TC counters. Which parameters were meant? Possibly 0x031E `mem_errors`.
21. **COM-012** gives an image volume of 50–200 MB, which contradicts the 4 MB frame.
22. **Ops-book EMG numbering:** renumber about 50 references to the simulator's numbering, or keep the book's numbering with its mapping table? *(E1-3.32)*

## C. Course design

23. **Week-2 Friday gate:** MCR or PDR? The SpaceCDF Gate Review tab checks MCR. *(E1-3.91)*
24. **Day-3 layout:** is `COURSE_PLAN` or `course_plan_expanded` canonical? The expanded one has no AOCS session.
25. **MCS round-robin:** 6 × 15 min (week-3 pack) or 9 × 12 min (ops workbook)? `positions.yaml` has 7 consoles. *(E1-3.63)*
26. **Reading lists:** what should students read for ops book §5.20 and §7.20 and instructor-book chapter 2? *(E1-4.26)*
27. **45 `[Claude Code: …]` placeholders** in the week-3 pack: fill them or delete them? *(E1-4.15)*
28. **WBS sums to 103 %** (facilitator book and OER §16.2.1). Which Level-1 share drops? The suggestion is Bus 30 → 27 %, then re-render `fig_wbs_tree.py`. *(E1-2.06)*
29. **Verification-method acronym:** ATID (ch 2.1) or IADT (ch 4.2)? *(E1-3.78)*
30. **Vibration and thermal test profiles:** sine 1.25 g or the 3.22 g crossover (OER ch 14 table vs note)? Which single random profile? Proto-flight TVAC at qualification temperatures? *(E1-3.85)*
31. **Back cover:** should "Senior Lecturer … leading the School" read "Associate Professor, SEDTI"? *(E1-4.33)*
32. **Is `github.com/FNewland/SpaceCDF` public** for OER readers?

## D. Tooling

33. **Explicit heading anchors `{#id}`:** may I add them to the EN and FR manuals and the PUS reference, and teach the MCS manual viewer to hide them? That makes French in-document links work. *(E1-4.37)*
34. **Rewrite `software_architecture.md`?** It describes Redis inter-process messaging, which no package uses, plus a stale diagram, file tree and data rates. *(E1-3.25)*
35. **French procedure wording:** cards with real `**BRANCH:**` annotations now keep the neutral French « l'étape N s'applique ». Should the checker allow « passer à l'étape N » when the card declares a matching BRANCH?
