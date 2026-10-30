# Harmonisation of the French corpus (packet G1)

*2026-10-28. Applies to every French file produced by packets F1–F5, O1–O5, W1, W2, Y1, P1–P3, M1–M2, D1a/D1b/D2, OER1–OER5 and the UI catalogs. Binding together with `glossary.csv` (terms) and `STYLE_FR.md` (form; new §20 summarises the rulings below).*

## 0. Scope, method, results

**Files edited** (139 EN/FR document pairs, plus catalogs and the overlay):
* Course books, edited in place in `out/course_fr/*.md`. The packet copies in `xlate/{F*,O*,W1,W2/*}/fr.md` are now stale, as agreed.
* Week 3 pack: `xlate/W2/{breakpoint_spec,peer_review_worksheets,sim_*_instructor,student_*,training_day1,training_day2}/fr.md`.
* SMO: `configs/eosat1/i18n/fr/{procedures,manual}/**`, `docs/fr/*.md`, overlay `configs/eosat1/i18n/fr/db.yaml` (only `fr` values changed, through `tools/i18n/overlay.load_db`/`save_db`; the round trip is byte-identical), and the MCS catalog `packages/smo-mcs/.../modern/i18n/fr.json`.
* CDF: `docs/oer/fr/chapters/*.md`, `docs/fr/*.md`, `docs/course/fr/*.md`, `frontend/src/i18n/locales/fr.c3.json`, and `components/FMECAPanel.tsx`.

**How the edits were made.** Replacements were scripted with `harmonise.py` (in the G1 scratchpad). The script masks fenced code (including fences inside blockquotes), inline code, display and inline maths (using the same pairing rule as mdparity), link targets, URLs, HTML comments and tags, and `{: }`/`{# }` attribute blocks. Every rule that depends on meaning only fires in paragraphs whose aligned English paragraph contains the trigger word. Examples: « point d'arrêt » is changed only where the EN says *breakpoint*; « palier »/« barreau » → « échelon » only where the EN says *rung* and not *tier*; « Point clé » → « Idée essentielle » only where the EN says *Key insight*. All 139 pairs align block for block, which is what makes these conditions possible. Each match was logged with its context and the log was reviewed before the rules were applied. Edits that needed a person's judgement (UI labels, position names, English titles left in prose) were applied from an explicit list of old→new strings. Each entry asserted its expected match count. Gender and number agreement was checked at every substitution point; for example, « un dossier de préparation » became « réunit les fiches de préparation », and « le maintien solaire sûr » became « l'attente sûre au Soleil ».

**Replacements per decision** (documents + overlay + catalogs):

| # | Decision | Replacements |
|---|---|---|
| D1 | Procedure titles (§1) | 91 (docs 85, overlay 6) |
| D2 | Position names (§2) | 43 (docs 35, overlay 6, MCS catalog 2) |
| D3 | Callout and card labels (§3) | 172 |
| D4 | Book titles, running heads, footer, briefing (§4) | 6 |
| D5 | Part and appendix titles (§5) | 3 |
| D6 | breakpoint → point de reprise (§6) | 22 |
| D7 | Currency (§7) | 183 |
| D8 | UI labels cited in books (§8) | 66 |
| D9 | Other cross-packet terms, first pass (§9) | 114 (docs 93, overlay 21) |
| D10 | Other cross-packet terms, second pass (§9) | 34 (docs 32, overlay 2) |
| — | FMECAPanel plural (§10) | 1 code call, 1 key → 3 plural keys |
| | **Total** | **734** |

**Checks after editing:**
* `mdparity.py`: 136/139 pairs show PARITY OK. The other 3 carry only the accepted exceptions, which are unchanged: cm³/m² superscripts in the facilitator book (`numbers: missing 1 2 3 3 3`), 5×5 in the learner workbook (`extra 5 5 5`), and 24 h/24, 7 j/7 in the ops book (`extra 7 24`). **No new exception.**
* `python3 -m tools.i18n check`: smo 0 errors (168 warnings, all "untracked"); cdf 0 errors (51 warnings, same kind).
* `python3 -m tools.i18n build` was re-run in smo and gives 2447 keys in `fr.db.json`.
* CDF `npx tsc -b`: 105 errors, the same count as before, none in FMECAPanel. `npx vite build --outDir <scratch>` succeeds.

---

## 1. Procedure titles: canonical EN → FR table

The ID together with the shipped English title is the key. All five families use one French title per English title. Rules:
* « AOCS » in a title is prose, so it is written **SCAO** (STYLE §7 rule A keeps AOCS for the console position and identifiers).
* « Recovery » becomes « Reprise après … » / « Reprise par … », except CTG-003, which keeps « Rétablissement » (glossary, majority).
* « health check » becomes **bilan de santé**.
* A different English title for the same ID (in the ops-book cards or in older text) gets its own faithful translation, listed under "Other EN forms".

### LEOP
| ID | EN (shipped) | FR canonical | Replaced variants (packets) |
|---|---|---|---|
| LEOP-001 | First Acquisition of Signal & OBC Boot | Première acquisition du signal et amorçage de l'OBC | — |
| LEOP-002 | Initial Health Check | Bilan de santé initial | Contrôle de santé initial (W2) |
| LEOP-003 | Initial Orbit Determination | Restitution d'orbite initiale | — |
| LEOP-004 | Solar Array Verification | Vérification du générateur solaire | — |
| LEOP-005 | Sun Acquisition | Acquisition du Soleil | — |
| LEOP-006 | Time Synchronisation | Synchronisation temporelle | *Time Sync* left in English (O1) |
| LEOP-007 | Sequential Power-On | Mise sous tension séquentielle | *Sequential Power-On* left in English (O1) |

### COM
| ID | EN (shipped) | FR canonical | Replaced variants / other EN forms |
|---|---|---|---|
| COM-001 | EPS Power System Checkout (book: EPS Checkout) | Vérification de l'EPS | Vérification du sous-système d'alimentation EPS (O4a, M2) |
| COM-002 | TCS Verification | Vérification du TCS | — |
| COM-003 | AOCS Sensor Calibration | Étalonnage des capteurs SCAO | Étalonnage des capteurs AOCS (O3, O4a, P1, Y1) |
| COM-004 | AOCS Actuator Checkout | Vérification des actionneurs SCAO | … actionneurs AOCS (O3, O4a, P1, Y1) |
| COM-005 | AOCS Mode Transitions | Transitions de modes SCAO | Transitions de mode(s) AOCS (O4a, P1, Y1) |
| COM-006 | TTC Link Verification | Vérification de la liaison TTC | — |
| COM-007 | OBDH Checkout | Vérification de l'OBDH | — |
| COM-008 | FDIR Configuration & Protection Functions | Configuration de la FDIR et fonctions de protection | Other EN forms: FDIR Configuration → Configuration de la FDIR; FDIR Configuration & Test (ops-book card) → Configuration et essai de la FDIR |
| COM-009 | Payload Power On | Mise sous tension de la charge utile | — |
| COM-010 | FPA Cooler Activation | Activation du refroidisseur du FPA | Mise en route du refroidisseur du FPA (O3, Y1) |
| COM-011 | Payload Calibration | Étalonnage de la charge utile | Other EN form: Payload Radiometric Calibration → Étalonnage radiométrique de la charge utile |
| COM-012 | First Light | Première lumière | *First Light* left in English (F5 prose and index) |
| COM-013 | ADCS Commissioning Closure & NOMINAL Declaration | Clôture de la recette du SCAO et déclaration NOMINAL | Other EN form: ADCS Full Commissioning (ops book) → Recette complète du SCAO |

### NOM
| ID | EN (shipped) | FR canonical | Replaced variants / other EN forms |
|---|---|---|---|
| NOM-001 | Pass Startup | Ouverture de passage | — |
| NOM-002 | Imaging Session | Séance de prise de vue | — |
| NOM-003 | Data Downlink | Transmission des données au sol | Vidage des données (O4a, Y1). A downlink is not a dump. |
| NOM-004 | Orbit Maintenance Manoeuvre Planning | Planification d'une manœuvre de maintien d'orbite | — |
| NOM-005 | HK Configuration | Configuration HK | — |
| NOM-006 | Software Upload | Chargement de logiciel | chargement de logiciel à bord (O2); *Software Upload* left in English (O1). Other EN form: Software Upload / Parameter Update → Chargement de logiciel / mise à jour de paramètres |
| NOM-007 | Momentum Management | Gestion du moment cinétique | Other EN form: … (Desaturation) → … (désaturation) |
| NOM-008 | Clock Synchronisation | Synchronisation de l'horloge | Synchronisation d'horloge (O4a, P3, Y1). Follows STYLE §13/§18 example 3. |
| NOM-009 | Routine Health Check | Bilan de santé de routine | Contrôle de santé de routine (W2) |
| NOM-010 | Eclipse Transition | Transition d'éclipse | — |
| NOM-011 | Data Rate Change | Changement de débit | — |
| NOM-012 | Shift Handover | Passation de consignes | Other EN form: Shift Handover Template → Modèle de passation de consignes |
| NOM-013 | Orbit Maintenance Manoeuvre Execution | Exécution d'une manœuvre de maintien d'orbite | — |
| (book) | Pass Plan Upload | Chargement du plan de passage | — |
| (book) | Long-Term Trend Review | Revue des tendances à long terme | — |

### CTG
| ID | EN (shipped) | FR canonical | Replaced variants / other EN forms |
|---|---|---|---|
| CTG-001 | Under-Voltage Load Shed | Délestage sur sous-tension | — |
| CTG-002 | AOCS Anomaly Recovery | Reprise après anomalie SCAO | Reprise après anomalie AOCS; « CTG-002 Anomalie AOCS » → Anomalie SCAO (O4a) |
| CTG-003 | TTC Link Loss Recovery | Rétablissement après perte de liaison TTC | Reprise après perte de liaison TTC (O4a, M2 CON-004) |
| CTG-004 | Thermal Exceedance | Dépassement thermique | — |
| CTG-005 | EPS Safe Mode | Mode survie EPS | EPS Safe Mode Recovery → Reprise après mode survie EPS |
| CTG-006 | Payload Anomaly | Anomalie charge utile | — |
| CTG-007 | Reaction Wheel Anomaly | Anomalie de roue de réaction | — |
| CTG-008 | Star Tracker Failure | Panne du senseur stellaire | — |
| CTG-009 | Solar Array Degradation | Dégradation du générateur solaire | — |
| CTG-010 | OBDH Watchdog Recovery | Reprise après chien de garde OBDH | Reprise sur chien de garde OBDH (O4a); Reprise après déclenchement du chien de garde OBDH (O4b) |
| CTG-011 | OBC Redundancy Switchover | Basculement sur l'OBC redondant | Basculement redondant de l'OBC (O4b) |
| CTG-012 | Overcurrent Response | Traitement d'une surintensité | Traitement des surintensités (O4a); *Overcurrent Response* left in English (O1) |
| CTG-013 | Battery Cell Failure | Défaillance d'un élément de batterie | — |
| CTG-014 | BER Anomaly | Anomalie de TEB | — |
| CTG-015 | Corrupted Image Recovery | Reprise après image corrompue | Récupération d'(une) image corrompue (O4a, O4b) |
| CTG-016 | Memory Segment Failure | Défaillance d'un segment mémoire | — |
| CTG-017 | Bus Failure Switchover | Basculement sur panne de bus | Basculement après panne de bus (O2) |
| CTG-018 (now CTG-021) | Boot Loader Recovery | Reprise par le chargeur d'amorçage | Reprise du chargeur d'amorçage (O4b) |
| CTG-019 | No Telemetry at Pass Start | Absence de télémesure en début de passage | … au début du passage (P2a, W2); Absence de TM au début du passage (W2) → Absence de TM en début de passage |
| CTG-020 | Ground Station Antenna Failure | Panne d'antenne de station sol | — |
| CTG-021 | OBC Bootloader Recovery | Reprise par le chargeur d'amorçage de l'OBC | Reprise de l'OBC depuis le chargeur d'amorçage (O4b) |
| CTG-022 | CAN Bus Failure Isolation | Isolation d'une panne de bus CAN | — |
| CTG-023 | Progressive Load Shed | Délestage progressif | — |
| CTG-024 | Solar Panel Loss Response | Traitement de la perte d'un panneau solaire | — |
| CTG-025 | AOCS Sensor Loss Recovery | Reprise après perte de capteur SCAO | — |
| CTG-026 | AOCS Actuator Stuck Recovery | Reprise après blocage d'un actionneur SCAO | … actionneur AOCS |
| CTG-027 | GPS Time Synchronisation and AOCS Recovery | Synchronisation temporelle GPS et reprise SCAO | … reprise AOCS (O4a) |
| CTG-028 | Propulsion Anomaly | Anomalie de propulsion | — |

The ops book's own card numbering (ch. 14, "book numbering") gives some CTG IDs different English titles. Their French follows the same pattern: CTG-005 Battery Anomaly → Anomalie batterie · CTG-006 Propulsion Anomaly → Anomalie de propulsion · CTG-009 IMU / Gyro Anomaly → Anomalie IMU / gyro · CTG-011 Mass Memory ECC / Storage Anomaly → Anomalie ECC / stockage de la mémoire de masse · CTG-013 Solar Array Underperformance → Sous-performance du générateur solaire · CTG-016 Payload Mode Anomaly → Anomalie de mode de la charge utile · CTG-018 TC Reject Rate Anomaly → Anomalie du taux de rejet des TC.

### EMG
| ID | EN (shipped) | FR canonical | Replaced variants |
|---|---|---|---|
| EMG-001 | Emergency Safe Mode | Mode survie d'urgence | — |
| EMG-002 | Total Power Failure | Perte totale d'alimentation | — |
| EMG-003 | OBC Reboot | Redémarrage de l'OBC | Other EN form: Emergency OBC Reboot → Redémarrage d'urgence de l'OBC |
| EMG-004 | Loss of Communication | Perte de communication | Perte des communications (O3, M2) |
| EMG-005 | Loss of Attitude | Perte d'attitude | — |
| EMG-006 | Thermal Runaway | Emballement thermique | — |

The ops book uses its own EMG numbering (EMG-002 Loss of Attitude, EMG-003 Loss of Communication, EMG-004 OBC Reboot, EMG-005 Thermal Runaway, EMG-006 Total Power Failure). The French follows the English title, so the two numberings never mix titles.

**CON-/PROC- (manual 10_*, M2 only, no conflict apart from the rules above).** CON-004 → Rétablissement après perte de liaison TTC. CON-021 → Défaillance en cascade des capteurs SCAO. The other CON-/PROC- titles are as listed in M2 NOTES §2.

These titles are now identical in the procedure-file headings, the overlay `proc:*:name` (shown by the MCS), the ops book, the instructor book, the workbooks, the Week 3 pack and the manual.

---

## 2. Positions

| Concept | EN | Chosen FR | Rejected (packets) | Why |
|---|---|---|---|---|
| Console position label | Flight Director / FLIGHT DIRECTOR | **Direction de vol** / DIRECTION DE VOL | Direction du vol (MCS catalog, Y1 overlay); Directeur de vol as a desk name (M2 desk table and heading) | Glossary and STYLE §6 (epicene function label « direction de vol »). The **person** stays « directeur de vol (FD) ». |
| Console position label | Power & Thermal / POWER & THERMAL | **Puissance et thermique** / PUISSANCE ET THERMIQUE | Énergie et thermique (MCS catalog, Y1 overlay) | Glossary « power subsystem → sous-système de puissance » (CNES « S/S puissance »); M2 and the books already used it. |
| Console position label | Flight Dynamics | **Dynamique du vol** | English kept in books (O1, F5) | Overlay `pos:aocs:display_name`. STYLE §17 gives « dynamique du vol ». |
| Console position label | Payload Operations | **Opérations charge utile** | English kept (O1) | overlay |
| Console position label | FDIR / Systems | **FDIR / Systèmes** | English kept (O1, F5) | overlay |
| CDF position | Mission Analyst | **Analyste de mission** | Analyste mission (F1, OER1 Table 1.4) | majority (F5, OER5, D2) and natural French |
| CDF position | Communications / Comms Engineer | **Ingénieur télécommunications** | Ingénieur communications (F5, OER5 Part IV, D2) | F1/OER1; French subsystem name « télécommunications » |
| CDF position | Mission Operations / Mission Operations Engineer; Ground Segment / Ground Segment Engineer | Opérations de mission / Ingénieur opérations de mission; Segment sol / Ingénieur segment sol | — | Follows the EN form, which differs between Table 1.4 and Part IV. Not a conflict. |

In the books, the console display names (the `positions.yaml` names that the French UI shows through the overlay) follow §8: French label with the English in brackets at the first mention in a chapter, for example `eps_tcs` (« Puissance et thermique » [Power & Thermal]), and the French label alone after that. This was applied in facilitator Appendix B and in ops-book ch. 5, 6 and 7, including the Table 7.x "Nom affiché" column. Desk IDs (`eps_tcs`…) and call-signs (FD, EPS, AOCS…) are unchanged.

## 3. Callout and card labels (one rendering each)

| EN | FR | Rejected (packets) |
|---|---|---|
| **Recommended background.** | **Lectures préalables conseillées.** | glossary row « prérequis conseillés » (row corrected) |
| **Expected reading before this session.** (and every « Expected reading … ») | **Lectures attendues avant cette séance.** / **Lectures attendues.** / **Lectures attendues avant le jour 2.** | Lectures préalables attendues… (F2, W1); Lecture attendue… (F5, W2) |
| **Think about it.** | **Matière à réflexion.** | Question de réflexion (OER4) |
| **Industry practice.** / **Industry Practice:** | **Pratique industrielle.** / **Pratique industrielle :** | — (punctuation follows the source) |
| **Key insight:** (and Key architectural/design insight) | **Idée essentielle :** | Point clé (F3, F4, OER3), Point essentiel (W1), Enseignement clé (F2, OER2) |
| **Key lesson:** | **Leçon clé :** | Enseignement clé (O5) |
| **Key principle:** | **Principe clé :** | — |
| Key Takeaway (summary-table header) | Point clé | Point essentiel (F1, OER1) |
| Key Equations Reference (section) | Rappel des équations clés | Équations clés (F1) |
| **Key equation(s) — X** | **Équation(s) clé(s) — x**, lower case after the dash (sentence case) | capitalised after "--" (F2) |
| **Watch out.** / **Common mistake.** | **Attention.** / **Erreur fréquente.** | — |
| **Standard reference.** | **Référence normative.** | Norme de référence, Accès aux normes (D2) |
| **Sensitivity check:** | **Contrôle de sensibilité :** | Vérification de sensibilité (OER1), Analyse de sensibilité (W1) |
| **Pass.** (worked-check verdict) | **Conforme.** | Validé (OER3) |
| Editor's note | Note de la rédaction | Note de l'éditeur (O4a) — « éditeur » is the publisher |
| Possible negative outcomes / deviations: (card field) | **Issues défavorables possibles / écarts :** | Issues défavorables / écarts possibles (O4a) |
| Step / Action / TC / Code / Confirm / Notes | Étape / Action / TC / code / Confirmation / Remarques | Confirmé (O4b) |
| (FD call) | (annonce du FD) | (décision FD) (O4b) |
| Systems / Technical / Risk / Operations reviewer | Évaluateur système / technique / risques / opérations | Relecteur … (OER4) |
| Procedure header fields Position Lead / Cross-Position / Difficulty | Poste responsable / Postes associés / Difficulté | Poste pilote, Interpostes (P3); Niveau (P2a) |
| Monitor: / Check: (not parser keys) | Surveiller : / Contrôler : | Surveillance :, Contrôle : (P2a) |
| Wire: (encoding label, not a parser key) | Octets émis : | Codage binaire, Codage (P2a, P2b), Trame (P3), Octets transmis (M2) |
| Document ID | Référence du document | Identifiant du document (M2, D1b) |
| Full read-and-do checklist | Liste de vérification complète « lire et faire » | lire-et-exécuter (O4b) |
| Speed multiplier | Facteur d'accélération | Multiplicateur de vitesse (W2) |
| Space usage (observer worksheet) | Occupation de l'espace (worksheet title, W2) | Utilisation de l'espace (O3) |

## 4. Book titles, running heads, document names

| Item | Chosen FR | Rejected |
|---|---|---|
| Facilitator book (*SpaceCDF — A Course Textbook in Concurrent Spacecraft Design*) title | SpaceCDF — Manuel **du** cours de conception concourante d'engins spatiaux | Manuel de cours (F1) |
| its running head | SpaceCDF — Manuel du cours | SpaceCDF — Manuel de cours (F1) |
| its `footer-fr` | Manuel du cours SpaceCDF · 2026 | Manuel de l'animateur SpaceCDF · 2026 (copied from the source front matter: the book is the course textbook, not a facilitator guide) |
| Cited *SpaceCDF Textbook* | *Manuel du cours SpaceCDF* | *Manuel SpaceCDF* (W1) |
| Course Workbook | SpaceCDF — Cahier d'exercices du cours | — |
| Facilitator's Book / Instructor book / Learner's Workbook (document names) | Guide de l'animateur / Guide de l'enseignant / Cahier d'exercices de l'apprenant | — |
| Per-role / per-position background briefing | fiche (de préparation) — « réunit les fiches de préparation par rôle » | dossier (de préparation) (F5); STYLE §18 example 11 |

**Owner action:** the English source `drive_course/facilitator_book_expanded.md` has `footer-fr: "Manuel de l'animateur SpaceCDF · 2026"`. It should be changed to « Manuel du cours SpaceCDF · 2026 » so that the two files agree.

## 5. Part and appendix titles

| Book | Titles (unchanged unless noted) |
|---|---|
| OER *Conception concourante d'engins spatiaux* | Partie I — Fondements et conception · Partie II — Conception des sous-systèmes · Partie III — Intégration, vérification et opérations · Partie IV — Guide de référence des postes d'ingénierie · Partie V — Démonstrations à partir des premiers principes (checked in all chapter files and the front matter) |
| Facilitator book | Partie 1 — Conception d'un CubeSat · Annexe A — **Guide de référence des postes d'ingénierie** · Annexe B — **Guide de référence des postes d'opérations** · Annexe C — **Guide de référence de la vérification et des premiers principes** (changed from « Référentiel … » (F5), because the glossary reserves « référentiel » for *baseline*; this matches OER Part IV) |
| Ops book / back cover | Partie 2 — Opérations d'un CubeSat (STYLE §18 example 8); back cover Partie 1 / Partie 2 match |
| Week 3 workbook | Partie 5 — Cahier d'exercices de la semaine 3 d'OrbitNorth (as the source has it) |

The source text still refers to "Part 5" in the instructor book and the ops book where it means Part 2. This was flagged by O1 and W2 and is left as in the EN.

## 6. breakpoint

**breakpoint (simulator state) → « point de reprise »** (masculine, as « point d'arrêt » was). This is the instructor-console catalog term (`Breakpoints` → `Points de reprise`). 22 replacements of « point(s) d'arrêt », made only in paragraphs whose EN says *breakpoint*: W2 pack, instructor book, back cover, facilitator book, ops book, manual (12_time, software_architecture) and `docs/fr/README.md`. « point d'arrêt » remains only for the QRH **pause point** (O2).

## 7. Currency (one style per book; the same style in every book)

| Unit | Rule | Applied |
|---|---|---|
| Euro | **k€ / M€ / €** after the number, with NBSP: « 800 k€ », « 1,0 M€ », « ~50 €/h », « Coût (k€) » | kEUR → k€ 113; MEUR → M€ 3; « 800K EUR » → « 800 k€ » 23; « 1,0M EUR » → « 1,0 M€ » 18; « 10K--50K EUR » → « 10--50 k€ » 1; « 50 EUR » → « 50 € » 9 (facilitator book, OER ch. 10–18, learner workbook) |
| Dollar | **k$ / M$ / G$**; « $ CA » / « $ US » **only where the source states CAD/USD** (« 300 M$ CA », « 25 G$ US ») | « k$ US » / « $ US » added by F3 where the EN gives no currency → « k$ » / « $ »: 15. One line escaped (`k\$`) so that pandoc and mdparity do not pair two `$` as maths. |

The prefix/postfix `$` waivers noted by OER1 are unchanged, and none are needed.

## 8. UI labels cited in the books

Rule (STYLE §20):
* If the label **exists in a French catalog**, use the French catalog label with the English in parentheses at its first mention in each chapter, then the French label alone.
* If it has **no catalog entry**, keep the English exactly as the screen shows it (a French gloss may follow once).

| Catalog entries used (EN → FR) | Source catalog |
|---|---|
| Run Analysis → « Lancer l'analyse » · Requirements → Exigences · Functions → Fonctions · Parametric → Paramétrique · V&V Matrix → Matrice V&V · Equipment → Équipements · Interfaces · Review Gates → Jalons de revue | CDF `locales/fr*.json` |
| Breakpoints → Points de reprise · STALE → PÉRIMÉ · console position names (§2) | SMO instructor / MCS catalogs, overlay |

**Without a catalog entry, so kept in English:** Dashboard, Gate Review, Trade Studies, Pointing Budget, Link Budget, Spectrum Selector, Equipment Browser, Budget Breakdown, Cost Breakdown, Exports, Go fix, Generate from Objectives, Positions, Compliance, ConOps (Editor), Data Budget, Mission/System Architecture, Orbit Trade Advisor, Timing Budget, Engineering Budgets, Accept/Edit/Reject, Run Design, Start Session, Eng. Budgets, Project Mgmt, Orbit/Class Advisor.

66 edits:
* The F3/F4 ad-hoc French tab names (Tableau de bord, Bilan de pointage, Sélecteur de spectre, Catalogue d'équipements, Détail des bilans/coûts, Revue de jalon, « Corriger ») were changed back to the English screen labels.
* The W1 « French (English) » pattern was reduced to the English label.
* Catalog labels got their French form (« **Exigences** (Requirements) », « Paramétrique (Parametric) », « Matrice V&V (V&V Matrix) », « Équipements » (Equipment), « Lancer l'analyse » (Run Analysis)).

Labels in SMO books that have no modern-catalog key were left as they are (tab IDs `overview`, `eps`…; classic-UI labels).

## 9. Other cross-packet term conflicts (D9, D10)

| EN | Chosen FR | Rejected (packets) | n |
|---|---|---|---|
| rung (rate / load-shed ladder) | **échelon** (tier stays « palier ») | palier (F3, O4a, P1, P2a, P2b), barreau (W2, M1) | 44 (only where the EN paragraph says *rung* and not *tier*) |
| burn wire | **fil thermofusible** | fil à couper (O1, W2, Y1), fil à chaud (O5, M2), fil fusible (F4, OER), fil à brûler (D1b), fil thermique (P2a) | 23 + 2 overlay |
| latch valve | vanne à verrouillage | vanne à verrou (D1a), vanne d'isolement (Y1) | 1 + 12 overlay |
| dark frame / flat field | image d'obscurité / champ plat | image noire / champ uniforme (O5), trame d'obscurité (Y1) | 3 + 3 overlay |
| sun-safe hold | attente sûre au Soleil | maintien sûr pointé Soleil (W2), maintien solaire sûr (Y1) | 4 + 4 overlay |
| tumbling | culbutage (glossary) | rotation incontrôlée (O4b) | 3 |
| hot-wash | débriefing à chaud | retour à chaud (W2) | 1 |
| store-and-forward | stockage et retransmission | relais en mode différé (F1) | 2 |
| shock response spectrum | spectre de réponse au choc (SRS) | (SRC) (F4) | 1 |
| SDR | revue de définition du système (SDR) | revue de définition système (F1) | 1 |
| upload (image) | charger / chargement | téléverser / téléversement (P2b, F4; Québec-flavoured, glossary) | 7 |
| auto-TX hold-down | maintien automatique de l'émetteur (auto-TX hold-down) | temporisation de maintien de l'émission automatique (O2), maintien automatique de l'émission (W2) | 3 |
| amber (status colour) | orange (MCS alarm colours stay jaune) | ambre (F1, O1) | 5 |
| boot loop / boot inhibit | boucle d'amorçage / inhibition d'amorçage | boucle/inhibition de démarrage (O4b, P2a, P3) | 8 |
| customer bulletin | bulletin client | bulletin au client (W2) | 4 |
| heartbeat | signal de vie | battement de cœur (P3) | 2 |
| tick (simulation step) | pas de simulation (catalog « pas {{n}} ») | pas de calcul (W2), top (P3, left: in a clock context) | 6 |
| bootloader allowlist | liste d'autorisation du chargeur d'amorçage | liste des commandes autorisées … (P3) | 2 |
| shutter control (RSSSA) | interruption de service (shutter control) | contrôle d'obturation (W1) | 1 |
| under-voltage lockout | coupure sur sous-tension | verrouillage de sous-tension (P3) | 2 |
| packing factor | taux de remplissage | facteur de remplissage (W1) | 1 |
| trim burn | poussée de correction | poussée d'appoint (Y1) | 2 overlay |

**Recorded in the glossary but not rewritten.** These are context-dependent and the packets already split them by sense:
* gate: seuil (numeric) / condition (permissive) / verrou (interlock); « jalon » only for review gates.
* jitter: microvibrations (pointing) / gigue (timing).
* cue card: operator fiche aide-mémoire / instructor carte d'aide.
* figure of merit: facteur de mérite / G/T facteur de qualité.
* authority: efficacité for a cooler.

## 10. CDF FMECAPanel plural bug

`components/FMECAPanel.tsx` used `t('{{n}} single points', { n })`, which displayed « 1 points uniques » and also "1 single points" in English. It now calls `t('{{count}} single points', { count, defaultValue_one: '{{count}} single point' })`, following GUIDE §4. `fr.c3.json` replaces the old key with `…_one` « {{count}} point unique », `…_other` « {{count}} points uniques » and `…_many` « {{count}} de points uniques ». `tsc -b` still reports 105 errors, none of them new. The vite build passes.

## 11. Glossary and style guide

* `glossary.csv`: **695 → 1568 entries** (+873 merged from all 28 NOTES files, deduplicated on a normalised EN key).
  * 63 multi-packet conflicts were resolved. The rejected renderings are recorded in `note` as "not: … (packets)". `source` lists the packet IDs.
  * 37 proposals already present in the glossary were dropped (the glossary wins).
  * 4 existing rows were amended: recommended background, SMART (course expansion: pertinente, traçable), facilitator (footer note), flight director (desk label « Direction de vol »).
  * The original CRLF line endings are kept.
  * The file is copied to `smo/tools/i18n/glossary.csv` and `cdf/tools/i18n/glossary.csv`.
* `STYLE_FR.md`: §12 now lists the fixed callout renderings, and the new §20 summarises these rulings. Copied to both `tools/i18n/`.

## 12. Parity exceptions

There are **no exceptions other than the three accepted ones**: cm³/m² in the facilitator book, 5×5 in the learner workbook, and 24 h/24, 7 j/7 in the ops book.

## 13. Left for the owner

* Packet copies `xlate/*/fr.md` (F, O, W1, and W2 instructor_book / week3 workbook / back_cover) are stale against `out/course_fr`. Rebuild from `out/course_fr` if anything reads them.
* `footer-fr` in the EN source of the facilitator book (§4).
* Paragraphs where the EN uses both *rung* and *tier* were not rewritten automatically. A few « palier » for *rung* may remain there.
* Procedure header *values* (`Sous-système : Propulsion / Flight Dynamics`, ALL, NOMINAL…) stay English per P3. No code reads them, so they can be translated if the owner confirms.
* `i18n accept --init` has still not been run in either repo, which is the source of all the "untracked" warnings.
