# Independent QA review: EN→FR translation (books, OER, SMO procedures/manual/docs, UI catalogs)

Reviewer: independent bilingual reviewer (European French, aerospace). Date: 2026-10-28. This was a read-only audit: no translated file was modified.
Scope: 124 Markdown pairs (6 course books, 24 OER chapters, 67 procedures, 19 manual files, 8 docs) plus 11 UI catalogs (5,299 strings). In total that is about 536k EN words and 648k FR words.
Out of scope: terminology consistency across files, which another agent is harmonising. A terminology point is reported here only when it changes meaning or is technically wrong.

## 1. Method (reproducible)

- **Alignment.** Each EN/FR pair was split into sections at its headings. The heading sequences match in all 124 pairs. `smo/configs/eosat1/manual/09_command_reference.md` has no FR file; this is intended, because it is generated from the YAML overlay (see PLAN.md).
- **Sampling.** Random seed `20261028` (`sample.py` in the reviewer's scratchpad). The sample has four parts:
  - **Book sections:** ≥5% of sections per document, with at least 3 per small file. That gives 230 sections and 34,508 EN words.
  - **Procedures:** 100% of 10 randomly drawn procedures (13,443 EN words): COM-010 fpa_cooler_activation, CTG-017 bus_failure_switchover, CTG-005 eps_safe_mode, CTG-011 obc_redundancy_switchover, CTG-024 solar_panel_loss_response, LEOP-003 initial_orbit_determination, NOM-008 clock_sync, NOM-009 routine_health_check, NOM-006 software_upload and NOM-001 startup.
  - **UI catalogs:** 150 random entries. The `fr.db.json` entries were checked against their EN text in `configs/eosat1/i18n/fr/db.yaml`.
  - **Reading:** every sampled pair was read in full, about 49k EN words.
- **Automated sweeps** over **all** FR Markdown and catalogs:
  - residual English, checked at line level and at paragraph level;
  - typography;
  - decimal-comma policy;
  - forbidden step jumps;
  - the STYLE_FR §17 list;
  - "tu";
  - targeted term sweeps;
  - `mdparity.py` on every pair;
  - a line-aligned check of negations and comparison operators in procedures, manual and docs.

## 2. Verdict

**Publishable after the listed fixes.** No CRITICAL defect was found, either in the sample or in the automated checks:
- no negation was flipped;
- no number, unit or limit was changed;
- no step order or condition was altered;
- the parsed procedure keys are intact.

The translation is accurate, idiomatic and technically literate, well above typical professional output.

Fix the 2 recurring MAJOR term errors in the procedures before operator use: « recommander » used for *re-command*, and « télémétrie » used for *ranging*.

**Defect rate in the sample (about 49k EN words):**

| Severity | Count | Per 1000 words |
|---|---|---|
| Critical | 0 | 0 |
| Major | 9 | 0.18 |
| Minor | 24 | 0.49 |
| **Total** | **33** | **≈0.7** |

## 3. Scores (1–5)

| Document | Accuracy | Fluency | Terminology | Typography | Notes |
|---|---|---|---|---|---|
| facilitator_book_expanded (course textbook) | 5 | 4.5 | 4 | 4.5 | « résolution au sol » for GSD; « mémoire statique » |
| orbit_north_week3 (ops book) | 4.5 | 4.5 | 4 | 4.5 | GSD; one ambiguous decision line (§4 M8) |
| learner_workbook_expanded | 5 | 4.5 | 4.5 | 4 | 27 `&nbsp;` entities (mirrors the EN source) |
| orbit_north_week3_workbook | 5 | 4.5 | 4.5 | 4.5 | « fin de semaine » |
| instructor_book | 4.5 | 4.5 | 4 | 4.5 | faithfully reproduces EN garbles (§7) |
| back_cover | 4 | 4.5 | 4 | 5 | invented French name for SEDTI |
| OER chapters (24) | 5 | 5 | 4.5 | 5 | best of the set; GSD and solid-state storage terms |
| SMO procedures (67) | 4.5 | 4.5 | 4.5 | 4.5 | « recommander », « télémétrie », % spacing |
| SMO manual (18) | 5 | 4.5 | 4.5 | 4.5 | — |
| SMO docs/fr (8) | 5 | 4.5 | 4.5 | 4.5 | many English pseudo-code blocks (by policy) |
| UI catalogs (11) | 5 | 4.5 | 4.5 | 4.5 | 7 near-identical strings, all legitimate; a few % spacing slips |

## 4. MAJOR findings (sample, plus the same pattern found by the sweeps)

The two procedure-term fixes (M1–M2 and M3–M4) take priority before operator use.

| # | Location (FR file:line) | EN | FR | Fix |
|---|---|---|---|---|
| M1 | smo/configs/eosat1/i18n/fr/procedures/commissioning/fpa_cooler_activation.md:165 | "re-command the setpoint with `PAYLOAD_COOLER_SETPOINT`" | « recommander la consigne avec … » (reads as *recommend*) | « commander de nouveau la consigne avec … » |
| M2 | same file:169; also contingency/star_tracker_failure.md:126 and leop/sun_acquisition.md:90 (sweep) | "re-command the setpoint / re-commanding by hand / re-commanding the mode" | « recommander la consigne / de recommander le mode à la main / recommander le mode » | « commander de nouveau » / « renvoyer la commande de mode » |
| M3 | procedures/leop/initial_orbit_determination.md:113; also nominal/shift_handover.md:103 « séance de télémétrie » | "ground-based range/Doppler" / "ranging session" | « la télémétrie et le Doppler sol » (Canadian readers take « télémétrie » to mean *telemetry*; the doc uses « télémesure ») | « les mesures de distance et Doppler sol » / « séance de mesure de distance » |
| M4 | smo_common/ui/i18n/fr.db.json key `tc:TTC_RANGING_START:description` | "Begin ranging sequence (requires frame sync)" | « Lancer une séquence de télémétrie … » | « Lancer une séquence de mesure de distance (ranging) … ». The ops book already glosses it this way (orbit_north_week3.md:2340, 2357). |
| M5 | out/course_fr/orbit_north_week3.md:4763 (a pitfall about confusing two quantities) | "the ground sample distance (29.3 m, a per-pixel figure)" | « la résolution au sol (29,3 m …) » | « la distance d'échantillonnage au sol (GSD, 29,3 m …) ». GSD is not resolution. The same error appears 19× in 10 files (sweep), e.g. OER 00_front_matter.md:27, 22_derivations.md:241 and manual 06_payload.md:26, while OER 05_requirements.md:43 uses the correct term. |
| M6 | cdf/docs/oer/fr/chapters/06_functional_decomposition.md:195; also :82 and facilitator_book_expanded.md:2876, :2993 | "≥ 32 GB solid-state storage" | « mémoire statique ≥ 32 Go » (that means SRAM) | « mémoire de masse à semi-conducteurs (flash) ≥ 32 Go » |
| M7 | out/course_fr/back_cover.md:53–54 | "School of Engineering Design and Teaching Innovation (SEDTI)" | « École d'innovation en conception et en enseignement du génie (SEDTI) » | Use the official name « École de conception et d'innovation pédagogique en génie (ECIPG) » (uOttawa site). STYLE §17 says official names must stay as published. |
| M8 | out/course_fr/orbit_north_week3.md:4185 | "RSSI -111 dBm, margin 2 dB: pass margin gate but log a low-margin caution" | « le seuil de marge est franchi, mais … » (« seuil franchi » reads as *limit violated*) | « la marge satisfait au critère (gate), mais consigner … » |
| M9 | English pseudo-code blocks: 46 untagged or `text` fences kept in English. Examples: OER 06_functional_decomposition.md:118–137 (function trees), OER 08_architecture_interfaces_budgets.md:252 (interface requirements "The EPS shall…"), OER 13_equipment_and_bom.md:30 (decision framework), OER 18_operations_and_fdir.md:262, docs/fr/OPERATIONS_GUIDE.md (5 blocks), PUS_SERVICE_REFERENCE.md (11 blocks) | — | Kept in English because mdparity requires fences to be byte-identical | This is a policy gap, not a translator error. French learners get English teaching content. Recommendation: let mdparity whitelist untagged/`text` fences and translate them. Real code (python/yaml/bash) stays English. |

## 5. MINOR findings (sample; representative)

| # | Location | Issue | Fix |
|---|---|---|---|
| m1 | procedures/contingency/bus_failure_switchover.md:125 (pattern ×156 across all files) | « Escalader immédiatement vers » (anglicism) | « Faire remonter immédiatement au … ». Note: fpa_cooler_activation.md:163 already does this. |
| m2 | procedures/contingency/obc_redundancy_switchover.md:152 (pattern ×13) | « Investiguer depuis le chargeur d'amorçage » | « Poursuivre l'analyse depuis … » |
| m3 | procedures/contingency/solar_panel_loss_response.md:55, 73, 76, 107, 141, 158–159, 170 | « 15% », « < 50% » in prose: no NBSP before % | « 15 % », « 50 % » |
| m4 | procedures/nominal/clock_sync.md:81 | « NE PAS faire sauter une horloge asservie » (could read as *blow up*) | « NE PAS appliquer de saut à une horloge asservie » |
| m5 | procedures/nominal/software_upload.md:2 | « OBDH / Memory Management » left untranslated | « OBDH / gestion mémoire » |
| m6 | procedures/nominal/software_upload.md:182 | « le chargement est nul » | « le chargement est caduc » |
| m7 | procedures/nominal/startup.md:56 | « Si le redondant échoue aussi » | « Si le transpondeur redondant échoue aussi » |
| m8 | procedures GO/NO-GO lines: commissioning/aocs_mode_transitions.md:67 (0,1°), commissioning/ttc_link_verification.md:151 (10,5 ± 0,5 dB), leop/time_sync.md:160 (1,0 s) | Decimal comma in operator thresholds; §4.2(3) says keep the point | 0.1° / 10.5 ± 0.5 dB / 1.0 s |
| m9 | fr.db.json `FEED FRESH` | « FLUX FRAIS » | « FLUX À JOUR » |
| m10 | fr.c1.json `Sponsor / Funder` | « Financeur » (drops "sponsor") | « Commanditaire / financeur » |
| m11 | fr.db.json `tm:ttc.tx_fwd_power` | « Puissance d'émission directe » | « Puissance d'émission incidente » |
| m12 | fr.c1.json ` \| Coverage: {{pct}}%`; fr.db.json `scn:eps_solar_panel_loss:briefing`, `scnresp:debris_impact_hermes3.1` (34 db strings with `\d%`) | % without NBSP | `{{pct}} %`, « 50 % » |
| m13 | OER 12_structures_propulsion_obdh.md:490, 493 | « file de téléchargement », « préparation du téléchargement » (downlink) | « transmission au sol » |
| m14 | manual 10_desk_procedures.md:186 and the following tables | "Time-Critical" → « Contrainte de temps » | « Critique en temps » |
| m15 | out/course_fr/instructor_book.md:839 | « La tête du senseur solaire grossier +X meurt » | « tombe en panne » |
| m16 | OER 24_back_matter.md:49 | Logo name changed to « GIA »; procedures keep « AIG » | Keep the proper name « AIG » |
| m17 | out/course_fr/orbit_north_week3_workbook.md:1539 | « Main courante de fin de semaine » (reads as *weekend* in Canada) | « Main courante hebdomadaire (fin de semaine de cours) » |
| m18 | docs/fr/LINK_BUDGET_AND_RATES.md:63 | « la synchronisation de verrouillage de la liaison montante » | « le délai d'accrochage de la liaison montante » |
| m19 | out/course_fr/facilitator_book_expanded.md:26 | "Per-role background briefings" → « Fiches de rôle » (loses "background") | « Fiches de cadrage par rôle » |
| m20 | out/course_fr/orbit_north_week3.md:4491 | « Basculer en croisé sur l'autre magnétomètre » | « Basculer (couplage croisé) sur l'autre magnétomètre » |
| m21 | procedures/nominal/routine_health_check.md:35 | « au soleil » (§3 requires « au Soleil », as used elsewhere) | « au Soleil » |
| m22 | out/course_fr/learner_workbook_expanded.md:1005, 1258, 1264, 1274 (27 total) | `&nbsp;` HTML entities. They mirror the EN layout, but §3 forbids entities | U+00A0 characters, or leave as layout and document the exception |
| m23 | procedures/contingency/solar_panel_loss_response.md:108 and 10 other cards | « étape suivante : étape 5 » is grammatically odd | « … l'étape 5 s'applique », the form most cards use |
| m24 | out/course_fr/orbit_north_week3.md:4199 | « Sauter l'étape 5 » | Acceptable in the ops book, which no parser reads. In procedures it would be forbidden; none was found there. |

## 6. Automated sweeps (all FR files)

**a. Residual untranslated English prose.**
- **Lines** with ≥6 English stop-words, outside code, quotes and voice-loop callouts: **0** in every file. The detector was validated on EN, where it finds 378 lines in the ops book.
- **Paragraphs** (wrapped text): 4 hits, all legitimate. These are HTML-comment SVG descriptions in facilitator_book_expanded.md:8070 and :8873 (kept by §11) and a table of OK/NOT-OK console tokens.
- **UI strings identical to their EN source:** 7 outside the database (`LEO SSO`, `UHF/VHF duplex`, `FOV (deg)`, `Latitude (deg)`, `Longitude (deg)`, `Allocation ({{unit}})`, `param 0xHHHH`), all acceptable. In `fr.db.json`, 73, all machine predicates such as `aocs.mode == 4`.
- **English kept by policy:** 46 pedagogical code blocks (see M9) and English citation titles.

**b. Typography.** U+202F and U+00A0 are applied systematically.
- Missing NNBSP before `; ! ?`: 74 hits, almost all inside quoted English voice callouts or LaTeX/pipe tables; about 5 are genuine.
- Colon without NBSP: 70 hits, almost all in English book titles inside references ("Space Mission Engineering: The New SMAD").
- Guillemet spacing errors: 0.
- `&nbsp;` entities: 27, all in learner_workbook and mirroring the EN.
- Straight double quotes in prose: 10, all in HTML comments, code or an inch mark (OER 03:308 `15"`).

**c. Decimal-comma policy.**
- Commas inside code: **0 real** cases. All 26 hits were false positives, matching across two spans or being `TM(9,2)` / `[0,0,1]` tuples. mdparity also confirms that every inline-code set is identical.
- Commas in procedure annotation lines: 4 real cases (m8), all on GO/NO-GO prose lines, none in a parsed backtick span.
- Points in book prose: 1,338 candidates. A 45-item sample showed they are section numbers, standard IDs or operator thresholds, all allowed by §4.2(3). No systematic violation.

**d. Forbidden step-jump wording in procedures** (« passer/aller/revenir/sauter … à l'étape N »): **0**. English `_PROSE_BRANCH` matches left in FR: **0**. The 23 EN cards with prose branches were reworded as « l'étape N s'applique » or « étape suivante : étape N ».
- Safety check: `server.py:_md_doc_response` confirms that FR procedures are **display only** and the runner reads English, so no gate bypass exists today.
- Recommendation: if FR ever feeds the runner, extend `_PROSE_BRANCH` to cover « l'étape \d+ s'applique » and « étape suivante : étape \d+ ».

**e. STYLE §17 Canadianisms.** 0 real occurrences of the listed Canadian forms. False positives:
- « RSSSA » appears only as an "(en anglais)" gloss next to LSTS;
- « modèle en V » appears only as a parenthetical alias of « cycle en V »;
- « boucle de rétroaction » (PROPULSION_GUIDE.md:124) is standard control-engineering French.

One borderline case: « fin de semaine » (m17). Also outside the list: « escalader » ×156 and « investiguer » ×13 (m1, m2).

**f. « tu ».** 0 occurrences in Markdown and catalogs. « vous » and the infinitive are used consistently, as §2 requires.

**g. Structural and numeric parity.**
- `mdparity.py`: 121 of 124 pass.
- The 3 failures are benign renderings: `cm^3`→`cm³`, `24/7`→« 24 h/24, 7 j/7 », and similar. No changed number was found.
- Line-aligned negation check (procedures, manual, docs): 82 candidates, every one correctly negated (« impossible », « sinon », « absence », « inefficace »). Comparison-operator mismatches: 30, all verbalised correctly (« dépasse », « sous »).

## 7. Source (EN) defects reproduced faithfully (owner action, not translation defects)

- instructor_book.md:531–532 (EN): garbled heading "Anomaly Cue Card Reference Anomaly Cue Cards" and the phrase "this shift and this shift".
- back_cover.md (EN): "seven major subsystems" followed by a list of eight.
- facilitator_book_expanded.md: captions of Tables 1.4.15 and 1.4.20 do not match the tables' content.
- manual 05_ttc.md:222 says `link_status` 1 = locked, while the rest of the corpus says LOCKED = 2.
- CTG-024 says "six solar panels on each face". The FR renders this sensibly as « un sur chaque face ».

## 8. Priority fix list

1. Procedures: replace « recommander » with « commander de nouveau » (4 places) and fix « télémétrie » for ranging (initial_orbit_determination.md:113, shift_handover.md:103, `fr.db.json` TTC_RANGING_START).
2. Books and OER: replace « résolution au sol » with « distance d'échantillonnage au sol (GSD) » (19 places) and « mémoire statique » with « mémoire de masse à semi-conducteurs » (4 places).
3. back_cover: use the official ECIPG name.
4. ops book line 4185: fix the ambiguous decision wording.
5. Policy decision on translating `text` pseudo-code blocks (46).
6. Batch minor fixes: anglicisms (escalader, investiguer), % NBSP, the GO/NO-GO decimal points, and the AIG logo name.
