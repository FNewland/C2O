# Guide de style — traduction française (français international / européen)

*Version 1.0 — 28 octobre 2026. Applies to every translation agent working on the SMO suite (EOSAT-1 simulator, MCS, planner, RF simulator, instructor console), SpaceCDF, the « Concurrent Spacecraft Design » open textbook, the ORBIT NORTH operations book, workbooks and facilitator/instructor books.*

This guide is written in English so that it binds every agent unambiguously; all examples of target text are in French. The terminology authority is `glossary.csv` in this folder. **When this guide and the glossary disagree, the glossary wins for a term; this guide wins for form (typography, numbers, markup).**

---

## 0. Ten rules to remember

1. Target is **international/European French**, not Canadian French. Replace Canadian house usage (§17).
2. **Identifiers never change** — mnemonics, parameter IDs, enum names, PUS service IDs, APIDs, procedure IDs, file names, call-sign acronyms, anything in backticks or code blocks (§10–§13).
3. Engineering « budget » → **bilan** (bilan de masse, bilan de puissance, bilan de liaison).
4. Books: formal academic French, **vous**. UI and procedures: terse, **infinitive** for actions (« Acquitter », « Vérifier que… »).
5. Prose numbers: **decimal comma**, thin no-break space for thousands. **Machine values keep the point** (§4).
6. Unit after a number: **no-break space** (`12 ppm`, `20 °C`, `5 %`).
7. « Guillemets » with **narrow no-break space** inside; narrow no-break space before `;` `!` `?`; no-break space before `:`.
8. Never touch LaTeX math except words inside `\text{…}` that are real words (§9).
9. Never touch Markdown attribute blocks `{: …}` / `{#…}`, HTML comments, front-matter keys, URLs, image paths (§11).
10. In `configs/eosat1/procedures/**`, keep the parsed annotation keys `**TC:**`, `**Verify:**`, `**LABEL:**`, `**BRANCH:**`, `**GO/NO-GO:**`, `**Action:**`, `**Note:**` in English, and never express branching in French prose (§13).

---

## 1. Authorities and source keys used in `glossary.csv`

| Key | Authority | Use |
|---|---|---|
| `JO` | FranceTerme / *Journal officiel*, Commission d'enrichissement de la langue française, *Vocabulaire de l'espace* (2013 compilation) | Primary for general space vocabulary. Binding on French State services only; we depart from it where CNES/ESA engineering usage differs, and the note says so. |
| `JO2020` | *Journal officiel* 26/09/2020 space list (engin spatial, désorbitation, retrait de service, objet orbital…) | Primary. |
| `CNES` | Usage in CNES documents (e.g. CNES nanosatellite Phase 0 presentation; CNES Universpace CIC programme) | Primary for engineering terms. |
| `ISAE` | ISAE-SUPAERO, *Management des systèmes spatiaux* (phases, revues) | Primary for project phases and reviews. |
| `N7` | INP-ENSEEIHT, *CubeSat platform: an introduction* (French course) | Corroborating academic usage. |
| `UIT` | ITU-R Recommendations, French versions (PIRE, TEB, affaiblissement en espace libre, station terrienne) | Primary for RF/regulatory. |
| `ESA` / `CCSDS` / `ECSS` | ESA French-language communication; CCSDS and ECSS standards (English-only — French terms come from CNES/AFNOR practice) | Standards names and numbers stay in English. |
| `HOUSE` | The owner team's existing French texts (`cdf/docs/orbit_north/syllabus_fr.md`, `recruitment_fr.md`) | Kept where already European-compatible; replaced where Canadian (§17). |
| `CODE` | Required by the SMO software (parsers, tests) | Non-negotiable. |
| `OWNER` | Owner ruling (identifiers stay English) | Non-negotiable. |
| `USAGE` | Established French aerospace/engineering usage, translator's judgement | Second-tier: confirm in IATE (iate.europa.eu) if in doubt. TERMIUM Plus is a secondary check only — reject its Canadian-only forms. |

Sources consulted for this version (verified 2026-10-28):
- FranceTerme, *Vocabulaire de l'espace* (2013): https://www.culture.gouv.fr/content/download/93742/file/voca_en_ligne_2013_spatial_def.pdf
- CELF, termes publiés au JO du 26/09/2020 (espace): https://www.culture.gouv.fr/content/download/294552/3371224?version=4 and FranceTerme record https://www.culture.fr/FranceTerme/terme/SPAT1782
- ISAE-SUPAERO, *Management des systèmes spatiaux*: https://pagespro.isae-supaero.fr/IMG/pdf/ManagementSystemesSpatiaux.pdf
- CNES, *Phases 0 nanosats pour la science* (Laurens): https://meteo-2018.sciencesconf.org/file/LAURENS_Phases_0_Nanosats_CNES.pdf
- CNES Universpace, programme CIC: https://universpace.cnes.fr/wp-content/uploads/programme-CIC.pdf
- INP-ENSEEIHT, *CubeSat platform: an introduction* (FR): https://odf-siteprod.inp-toulouse.fr/enseeiht/plugins/odf-web/odf-n7/_content/course-cubesat-platform-an-introduction-fr/Cubesat%20platform_%20an%20introduction.pdf
- ITU-R Recommendations, French editions (e.g. https://www.itu.int/dms_pubrec/itu-r/rec/s/R-REC-S.1716-0-200502-I!!PDF-F.pdf)
Entries marked `USAGE` were not individually verified online in this pass; spot-check contested ones in IATE before the first large batch.

---

## 2. Register and voice

| Text type | Register | Person / mood | Example |
|---|---|---|---|
| Textbook chapters, ops book, facilitator/instructor books | Formal academic French, impersonal or **vous** | Indicative; « on » sparingly; no « nous » of majesty except in the authors' preface | « Vous dimensionnerez ensuite la batterie pour le cas le plus défavorable. » |
| Learner workbook, worksheets | Direct, friendly-formal | **vous**, imperative for tasks | « Calculez la fraction d'éclipse pour β = 0°. » |
| Procedures (`procedures/**/*.md`, obcp YAML descriptions), checklists | Terse, operational | **Infinitive** for each action (« Vérifier », « Envoyer », « Consigner ») — standard French procedure style | « Consigner le temps bord T_obc. » |
| UI labels, buttons, menus | Minimal | Buttons and commands: **infinitive** (« Acquitter », « Enregistrer »); states: past participle or noun (« Acquitté », « En attente ») | `ACK ALL` → `TOUT ACQUITTER` |
| UI help text, tooltips, empty states | Short full sentences | Indicative, **vous** if addressing the operator | « Aucune donnée de télémesure pour l'instant. » |
| Voice-loop phraseology | Not translated (§16) | — | — |

Never use **tu**. Avoid anglicised syntax: passive chains, noun stacks (« contrôle de limites de surveillance bord » → restructure), « en termes de », « adresser un problème » (→ « traiter »), « supporter » for "support" (→ « prendre en charge »), « opérer » a satellite (→ « exploiter » / « piloter » ; « opérations » is fine as a noun), « éventuellement » for "eventually" (→ « finalement »), « digital » (→ « numérique »).

---

## 3. Typography (French, Imprimerie nationale conventions)

Characters: this file contains the real U+202F NARROW NO-BREAK SPACE and U+00A0 NO-BREAK SPACE characters wherever French requires them (they are invisible in most editors — inspect with a hex viewer). **Agents must emit the real characters**, never HTML entities (`&nbsp;`, `&#8239;`).

| Rule | Write | Not |
|---|---|---|
| Guillemets | « mode survie » (U+202F after « and before ») | "mode survie", « mode survie » with ordinary spaces |
| Quotes inside quotes | « … “…” … » | « … « … » … » |
| Before `;` `!` `?` | U+202F: `vrai ;` `GO !` `pourquoi ?` | `vrai;` |
| Before `:` | U+00A0: `Remarque :` | `Remarque:` |
| After `:` `;` | ordinary space | — |
| No space before | `.` `,` `)` `…` | — |
| Ellipsis | `…` (U+2026) | `...` |
| Apostrophe | straight `'` (U+0027) everywhere, for consistency with code, glossary and search; smart quotes may be applied at render time by the build | mixing ’ and ' |
| Dashes | keep the source's spaced em dash ` — ` for incises and in titles (« Chapitre 10 — Opérations LEOP ») ; en dash `–` for ranges | hyphen as dash |
| Capitals | No capitals on days, months, languages, nationalities used as adjectives (« jeudi », « août », « le français », « l'industrie canadienne »). Capitals on astronomical bodies in the astronomical sense: la Terre, le Soleil, la Lune. Accented capitals are mandatory: « ÉTAT », « À VENIR », « Équipe ». | « Etat », « A venir » |
| Headings | **Sentence case** (only first word and proper nouns capitalised) | English Title Case |
| Ordinals | 1er, 1re, 2e, 3e, XXIe (front matter may use `1<sup>er</sup>` as the house does) | 2ème, 2nd |
| Abbreviations | p. ex., c.-à-d., env., n°, cf., etc. (no ellipsis after etc.) | e.g., i.e. |
| Lists | Items introduced by a colon; items lower-case and ending with « ; » except the last « . » when they are fragments; full sentences keep capitals and full stops | — |
| Spelling | Rectified spelling not required; use traditional spelling consistently: événement, connaître, maître, coût. Ligatures œ/æ mandatory (manœuvre, nœud) | évènement, manoeuvre |

---

## 4. Numbers — the policy and why

**Principle.** A number is either *for reading* or *for typing/matching*. Numbers for reading follow French conventions; numbers that an operator types into the MCS, compares character-for-character with a console display, or that a program parses, stay exactly as in the source.

### 4.1 French format (decimal comma) — applies to
- running prose in all books and in the human-readable parts of manuals;
- tables of engineering values meant to be read (link-budget tables, mass budgets, trade matrices, worked-example results);
- figure captions and alt text;
- UI **static** text written by humans (help text, tooltips) when it contains a non-integer.

Format: decimal comma `3,5`; thousands grouped with U+202F from five digits (`86 400 s`, `12 345`), no grouping for four-digit numbers and years (`1695 km`, `2026`); ranges `3 à 22 ms` or `3–22 ms`; signs `+3,0 dBW`, `−174 dBm/Hz` (U+2212 minus in prose); scientific notation `1,991 × 10⁻⁷ rad/s` (or keep the LaTeX if the source used math, §9).

### 4.2 Source format (decimal point, unchanged) — applies to
1. Everything inside backticks or fenced code blocks (`` `obdh.time_ref` (0x0A13) = 2 ``, `` `HK_REQUEST(sid=4)` ``).
2. Everything inside parsed procedure annotations (`**Verify:** \`eps.bat_voltage >= 7.2\` (0x0101, timeout 10 s)`) — the parser reads them.
3. Command arguments, limits and thresholds that the operator types or reads off the console, wherever they appear (procedures, ops book, manual). Leave them exactly as in the source (decimal point). **Do not add backticks the source did not have**: the structural parity checker (`mdparity.py`) requires the inline-code set to be identical between EN and FR.
4. Telemetry values rendered by the UI code (the UI does not localise numbers; display and command entry must match).
5. Voice-loop transcripts that quote a value as read from the display: « FD, AOCS — pointing 0.28° (NADIR), nominal. » stays unchanged (§16).
6. LaTeX math (§9).
7. Hex IDs, version numbers, standard numbers, dates/times in ISO form (`2000-01-01T12:00:00`, `T+04:12`, `AOS-5 min`), CCSDS/PUS tuples `TM(9,2)`.

**Why:** the MCS command builder and the procedure parser accept only `.` as decimal separator and `,` as argument separator. A comma in `SET_SOC(78,5)` is a different command. Keeping the point wherever a value crosses the human/machine boundary — and the comma everywhere else — is the only rule that is both typographically French and operationally safe. A reader will see `7,2 V` in a textbook explanation and `` `7.2` `` in the procedure step that sets the limit; the backticks signal the difference.

### 4.3 Percent, angles, temperature
`78 %` ; plane angles take **no** space: `28°`, `10°` d'élévation ; temperatures do: `20 °C`, `150 K`.

---

## 5. Units and quantities
- SI symbols unchanged and never pluralised; U+00A0 between number and unit: `2 W`, `6 dBi`, `2,25 GHz`, `9600 bit/s`.
- Data: **bit** (bit, kbit/s, Mbit/s) and **octet** (o, ko, Mo, Go). « MB/day » → « Mo/jour » ; « Mb » → « Mbit ». Never « bps », never « MB » in French prose. Identifiers like `storage_mb` unchanged.
- Rotation: « tr/min » (UI may abbreviate to `tr/min` too; not « rpm »).
- Time-of-day in prose: `9 h 30`, `17 h` (U+00A0 around « h »); durations `90 min`, `8 h`, `30 s`. UTC/MET/ISO timestamps unchanged.
- Units in table headers in parentheses: « Masse (kg) ».
- « 1U, 3U, 6U » unchanged (no space). « 5 × 5 » with spaces.

---

## 6. Gender-inclusive writing

The European partners' and French administrative practice discourage the *point médian* (« invité·e·s ») in technical and pedagogical documents; the owner's syllabus uses it — **do not propagate it**. Use, in order of preference:
1. **Epicene wording**: « l'équipe », « les personnes participantes », « le corps enseignant », « la direction de vol », « chaque membre de l'équipe », « vous ».
2. **Function labels for positions**: console positions are *functions*, not people. In UI, procedures and the position reference, use the function noun or the masculine short form as a label (« FD — directeur de vol », « Ingénieur SCAO ») and state once, in each book's front matter: « Les intitulés de postes désignent des fonctions et s'appliquent indifféremment à toutes et à tous. »
3. **Full doublets** only in direct address and front matter: « les étudiantes et étudiants », « les animateurs et animatrices ».
Never use parentheses forms (« étudiant(e)s ») or slashes.

---

## 7. Acronyms

**Rule A — operational acronym stays English.** When the English acronym is what operators see on a console, say on the loop, or find in identifiers, keep it, with a French expansion **on first use per chapter**:
« le système de contrôle d'attitude et d'orbite (SCAO) » — but the console position and subsystem tab stay **AOCS**: first use « le SCAO (position AOCS sur la console) ».
Kept English: AOCS (position), EPS, TCS, OBDH, OBC, TT&C/TTC, FDIR, FDS, MCS, MPS, LEOP, AOS, LOS, MET, SoC, DoD, MPPT, PDU, MLI, FPA, SPF, TRL, ConOps, MoE/MoP/TPM, WBS, BOM, ICD, RID, CLTU, APID, SID, PUS, CCSDS, ECSS, FEC, LDPC, OWLT, RAAN, LTAN, SSO, LEO, TID, SEU, TLE, CDF, review acronyms (MCR, MDR, PRR, SRR, PDR, CDR, QR, AR, FRR, ORR, LRR, CRR, ELR).

**Rule B — genuine French acronym replaces the English one** where French technical literature (ITU-R French, AFNOR, JO) uses it universally: PIRE (EIRP), TEB (BER), RSB (SNR), AMDEC (FMECA), AMDE (FMEA), CEM (EMC), CCM (MCC, rarely needed), REX (lessons learned), UIT (ITU), ONU (UN), CUPEEA (COPUOS), ASC (CSA), ISDE (ISED), LSTS (RSSSA). First use: « AMDEC (FMECA) ». In UI labels, apply rule B too (EIRP → PIRE, BER → TEB).

**Rule C — reviews.** Keep the English acronym, expand in French using CNES/ISAE names: « revue de définition préliminaire (PDR) ». Mention the CNES acronym (RDP) only where comparing agency vocabularies.

**Rule D — plurals.** Acronyms are invariable: « des TC », « les OBC ». Gender follows the French head noun: « la TM » (télémesure), « une TC », « le SCAO », « l'EPS » (masc., le sous-système), « la PDR » (revue), « le MCS ».

---

## 8. Headings, captions, alt text, cross-references, links

- **Headings**: translate, sentence case, keep numbering and any trailing attribute block verbatim. `## 10.5 Momentum management and desaturation` → `## 10.5 Gestion du moment cinétique et désaturation`.
- **Fixed section names** (use exactly): Learning objectives → Objectifs d'apprentissage · Summary → Synthèse · Problems → Exercices · References → Références · Cited references → Références citées · Worked example → Exemple résolu · Key equations → Équations clés · Derivation → Démonstration · Verification (appendix) → Vérification · Session summary → Synthèse de la séance · Notes & Reflections → Notes et réflexions · Discussion prompts → Pistes de discussion · Decisions you own → Décisions qui vous reviennent · What you need to know first → Ce qu'il faut savoir d'abord · Formulas, charts, rules of thumb → Formules, abaques et règles empiriques · Common pitfalls → Écueils fréquents · Returning to UniSat-1 → Retour sur UniSat-1 · Real mission example → Exemple de mission réelle.
- **Captions**: `**Figure 11.5** —` → `**Figure 11.5** —`; `Table 7.4 —` → `Tableau 7.4 —`. Translate the caption text; numbers inside follow §4.1 (caption = for reading).
- **Alt text** (`![…](path)`): translate fully, it is read by screen readers; keep the path. Keep alt text informative, ≤ 250 characters.
- **Cross-references**: « Chapter 7 §7.4.1 » → « chapitre 7, §7.4.1 » ; « see Table 7.4 » → « voir le tableau 7.4 » ; « Part V » → « partie V » ; « Figure 1.4 » → « figure 1.4 » in running text (capital only at the start of a caption). Anchor IDs (`#sec-…`, `{#fig-…}`) never change.
- **Links**: translate link text, never the URL. Titles of cited works stay in the original language, in italics; a French gloss may follow in parentheses once.
- **Proper names**: SpaceCDF, SMO, EOSAT-1, EOSat-3U, UniSat-1, ORBIT NORTH, Brightspace, Cyber Range, ESA, NASA, CNES, mission names (CAPSTONE, MarCO, Hitomi, PROBA-2, Planet SuperDove), book titles (*SMAD*) — unchanged. Canadian institutions and laws use their **official Canadian French** names (they are proper names, not Canadianisms): Agence spatiale canadienne, ISDE, Loi sur les systèmes de télédétection spatiale, École de conception et d'innovation pédagogique en génie (ECIPG; EN: SEDTI).

---

## 9. LaTeX mathematics

- **Never** change symbols, operators, numbers, subscripts, spacing commands or structure inside `$…$` / `$$…$$`, including decimal points (`1.991 \times 10^{-7}`) — the derivations chapter and SpaceCDF code share these symbols.
- **Subscript labels** inside `\text{}` (`P_{\text{avg}}`, `\dot{\Omega}_{\text{req}}`, `f_{\text{duty,mode}}`, `T_{\text{disturbance}}`) are **symbols, not words: do not translate them**.
- **Translate `\text{}` only when it is running language or a unit annotation in words**: `\text{where}` → `\text{où}`, `\text{(per orbit)}` → `\text{(par orbite)}`, and acronyms covered by rule B: `\text{EIRP}` → `\text{PIRE}`. Unit annotations like `\text{(dBW)}` are unchanged.
- The prose around the formula uses §4.1 French numbers; accept that the formula keeps the point.

---

## 10. Code, inline code and identifiers

- **Inline code** (single backticks): never translated, never re-spaced. French punctuation goes outside: « … vaut `2` (GPS) ; … ».
- **Fenced code blocks** with a language tag (`python`, `yaml`, `json`, `bash`, `js`…): not translated **at all**, comments included, when the file lives under `smo/` or `cdf/` source/config trees. In **book chapters**, explanatory comments in code examples (`# compute FSPL in dB`) **are** translated (they are pedagogy); string literals and identifiers are not.
- Fenced blocks **without** a language tag or tagged `text` that contain human dialogue (voice-loop transcripts, sample log lines written by a person): translate the narrative, keep callouts, call-signs, values and timestamps unchanged (§16).
- Identifier list (DNT, see glossary `ident` rows): telecommand mnemonics, parameter IDs, hex IDs, enum names (modes, phases, states, rate tiers), PUS IDs (S3, TM(1,1)), func_id, SID, APID, procedure IDs, STEP labels, file names, API routes, keyboard key codes (`ArrowUp`), CSS classes, environment variables (`SMO_UI`).
- Where English enum names appear in prose, a French gloss may follow once: « en mode `DETUMBLE` (amortissement des vitesses angulaires) ».

---

## 11. Markdown structure, front matter, HTML

- Preserve verbatim: attribute lists `{: .part-divider}`, `{#id .class}`, HTML comments `<!-- … -->` (they carry build directives and SVG labels for maintainers), raw HTML tags and attributes, `<sup>`, table pipes and alignment rows, list markers and indentation, line breaks inside tables, footnote markers.
- **Inline SVG** in chapters: translate the text content of `<text>`/`<tspan>` elements only; keep attributes, IDs, comments. Check that the French label fits (French runs ~15–20 % longer); shorten rather than overflow.
- **Front matter (YAML)**: keys unchanged. Translate values of `title`, `subtitle`, `running`, `footer-fr`; set `language: fr`; keep `course-codes`, `brand`, `version`, `cover-image`, `toc`. `footer-en` stays English.
- Do not re-wrap lines in a way that moves annotation keys off the start of a line.

---

## 12. Callout boxes and admonitions

Blockquote callouts start with a bold label. Fixed renderings:
`**Recommended background.**` → `**Lectures préalables conseillées.**` · `**Key equations — …**` → `**Équations clés — …**` · `**Note.**`/`**Note:**` (books) → `**Remarque.**`/`**Remarque :**` · `**Warning**` → `**Attention**` · `**Tip**` → `**Conseil**` · `**Example**` → `**Exemple**` · `**Why it matters**` → `**Pourquoi c'est important**` · `**Step 1:**` (in books) → `**Étape 1 :**`. · `**Expected reading before this session.**` → `**Lectures attendues avant cette séance.**` (every « Expected reading … » → « Lectures attendues … ») · `**Think about it.**` → `**Matière à réflexion.**` · `**Industry practice.**` / `**Industry Practice:**` → `**Pratique industrielle.**` / `**Pratique industrielle :**` · `**Key insight:**` → `**Idée essentielle :**` · `**Key lesson:**` → `**Leçon clé :**` · `**Key principle:**` → `**Principe clé :**` · Key Takeaway (summary-table header) → Point clé · Key Equations Reference (section) → Rappel des équations clés · `**Watch out.**` → `**Attention.**` · `**Common mistake.**` → `**Erreur fréquente.**` · `**Standard reference.**` → `**Référence normative.**` · `**Sensitivity check:**` → `**Contrôle de sensibilité :**` · `**Discussion point.**` → `**Point de discussion.**` · `**Pass.**` → `**Conforme.**` · Editor's note → Note de la rédaction.
**Exception:** inside `configs/eosat1/procedures/**` keep `**Note:**` and `**Action:**` in English (§13).

---

## 13. Operations procedures (`configs/eosat1/procedures/**`, `obcp/*.yaml`, `fdir/procedures`)

The markdown procedures are both documents and machine input (`smo_common/procedures/schema.py`).
- **Keep exactly**: `**TC:**`, `**Verify:**`, `**LABEL:**`, `**BRANCH:**`, `**GO/NO-GO:**`, `**Action:**`, `**Note:**`; the first backtick span after each; the literal tokens `Service N, Subtype N`, `func_id N`, `timeout N s`, `max N`, `-> GO \`X\` | NO-GO \`Y\``; `STEP-n` labels; procedure IDs; `[ ]` checkboxes.
- **Translate**: the title after the ID (« # NOM-008 : Synchronisation de l'horloge »), section headings (Purpose → Objet ; Prerequisites → Prérequis ; Procedure Steps → Déroulement ; Step N --- … → Étape N --- … ; Off-Nominal Handling → Conduite à tenir hors nominal ; Post-Conditions → Postconditions), header field labels (`**Subsystem:**` → `**Sous-système :**`, `**Phase:**` → `**Phase :**`, `**Revision:**` → `**Révision :**`, `**Approved:**` → `**Approuvé par :**`) — these are not parsed; and all prose after the annotation keys.
- **Branching**: the safety gate detects *English* prose branching (« proceed to Step 3 », « skip to Step 5 ») and refuses to run such cards. French « passer à l'étape 3 » would **bypass that gate**. Therefore: never introduce step-jump wording in French prose; if the English source contains prose branching, keep the structured `**BRANCH:**` line, translate the prose as a description without a jump verb, and flag the file to the owner. Recommend extending `_PROSE_BRANCH` to French (`(?:passer|aller|revenir|sauter)\s+(?:à|à l'|aux?)\s+étape\s+\d+`) before procedures are translated.
- **Mirrored content**: `mcs/gonogo_matrix.yaml` ↔ `manual/10_desk_procedures.md` §« GO/NO-GO Call Matrix » are held identical by `tests/test_content/test_gonogo_matrix_mirror.py`. Translate both in the same change, identically, or neither.
- YAML: translate only human-facing values (`description`, `label`, `situation`, `fd_decision`, `title`, `notes`) and only when no code matches on the value. Never translate keys, IDs, `name:` of commands/parameters, enum values, or comments in config files (comments are developer documentation; they stay English).

---

## 14. UI strings

- Keep the case style of the source: ALL-CAPS labels stay all caps **with accents** (« ÉTAT », « PÉRIMÉ »). Title-case English labels become sentence case.
- Buttons/actions: infinitive (« Envoyer », « Acquitter », « Injecter une panne », « Figer »). States: participle/adjective (« Armé », « Envoyée », « Verrouillé »). Never a final full stop on labels.
- Length budget: aim ≤ 120 % of the English length; abbreviate with a full stop (« Puiss. », « Réch. bat. », « Tps propag. ») rather than overflow. Units and identifiers inside labels unchanged.
- Placeholders and interpolation: never alter `{name}`, `%s`, `${…}`, `—` placeholders, or HTML entities; respect the word order of the sentence around them.
- Accessibility strings (`aria-label`, `title`, skip links) are translated like visible text.
- Keyboard keys in prose: Entrée, Échap, Maj, Ctrl, flèche haut. Key codes in code unchanged.
- Severity ladder (fixed): Info · Avertissement · Alarme · Critique ; alarm colours: vert, jaune, rouge, gris.

---

## 15. Engineering prose conventions

- « shall » in requirements → « doit » ; « should » → « devrait » ; « may » → « peut ». Keep requirement IDs.
- « budget » → « bilan » except money (§0).
- Prefer nouns used in French practice over calques: « essai » (hardware test), « recette » (acceptance), « adaptation » (tailoring), « référentiel » (baseline), « jalon » (gate), « retour d'expérience » (lessons learned).
- « the spacecraft » → « le satellite » when it is EOSAT-1 or a CubeSat; « l'engin spatial » only for the generic notion.
- Do not translate quoted text from standards; paraphrase in French and keep the citation.

---

## 16. Voice-loop phraseology

Callouts are **spoken protocol**, like aviation radiotelephony phraseology, and must be identical across Canadian, Danish and French crews. They stay in English, in quotes, with the French meaning explained around them: « Comm check 1-2-3 », « Standby », « Standby plus 30 », « Go for X », « Hold », « Resume », « No-go », « AOS in N », « LOS », « Pass closed », « Anomaly, [paramètre], [valeur] », « Mark », « Loop discipline », « Copy », « hot mike on/off ». Call-signs (FD, AOCS, EPS…) unchanged. The address pattern `[DESTINATAIRE], [ÉMETTEUR] — [MESSAGE]` may have its placeholders translated, not its order.

---

## 17. Canadian house usage to replace

| Existing house term (syllabus/recruitment) | Status | European rendering |
|---|---|---|
| avant-midi | Canadian | matin / matinée |
| fin de semaine | Canadian | week-end |
| courriel | Fine (FranceTerme) | courriel — **decision: use « courriel », never « e-mail »** |
| rétroaction(s) | Canadian | retour(s), commentaires |
| débreffage | Québec (OQLF) | débriefing (formal: réunion-bilan) |
| leçons apprises | Calque | retour d'expérience (REX) |
| résultats d'apprentissage | Canadian | acquis d'apprentissage (keep in official uOttawa course documents only) |
| heures de bureau | Canadian | permanence |
| examen du concept de mission (MCR) | Calque | revue du concept de mission (MCR) |
| revue de conception préliminaire (PDR) | Calque | revue de définition préliminaire (PDR) |
| portail de revue | Calque | jalon |
| base de référence (des exigences) / base de planification | Canadian | référentiel (d'exigences) / référentiel de planification |
| matrice de personnalisation | Calque | matrice d'adaptation (tailoring) |
| modèle en V | Acceptable | cycle en V (preferred) |
| réponse aux anomalies | Calque | traitement des anomalies |
| livrer un cours / livré en présentiel | Calque | dispenser / se déroule en présentiel |
| naviguer les obligations | Calque | s'orienter parmi / maîtriser les obligations |
| dynamique de vol | Acceptable | dynamique du vol |
| ticket d'anomalie | Acceptable | fiche d'anomalie |
| invité·e·s, préparé·e·s (point médian) | Not used in European technical texts | epicene rewording (§6) |
| RSSSA (as a French acronym) | Wrong | LSTS (Loi sur les systèmes de télédétection spatiale) |
| quart (d'opérateur), répétition à blanc, registre des risques, étude de compromis, nomenclature, cahier d'exercices, conception concourante, bilan de liaison, station sol | European-compatible | keep |

uOttawa administrative names (course titles, regulations, « plan de cours », Brightspace) remain as officially published.

---

## 18. Before / after examples (from the real corpus)

**1. UI label and tooltip — MCS (`smo-mcs/static/modern/index.html`, `mcs.js`)**
> EN: `ACK ALL` · `0 UNACK` · `Time to SoC yellow limit` · `Blink is reserved for unacknowledged P1 and stops on acknowledgement.`
> FR: `TOUT ACQUITTER` · `0 NON ACQ.` · `Temps avant limite jaune du SoC` · `Le clignotement est réservé aux alarmes P1 non acquittées et cesse à l'acquittement.`

**2. Planner UI with placeholder text**
> EN: `CONTACT WINDOWS — NEXT 24 H` · `State of charge the constraint check assumes. Leave blank to use the server's configured default.`
> FR: `FENÊTRES DE VISIBILITÉ — 24 H À VENIR` · `État de charge supposé par la vérification des contraintes. Laisser vide pour utiliser la valeur par défaut du serveur.`

**3. Procedure step — NOM-008 (`procedures/nominal`)**
> EN:
> ```
> ### Step 1 --- Read the Onboard Clock and Its Time Reference
> **LABEL:** `STEP-1`
> **TC:** `REQUEST_TIME` (Service 9, Subtype 2) --- explicit TM(9,2) time report
> **Verify:** `obdh.mode == 0` (0x0300, timeout 10 s) --- NOMINAL
> **Note:** Record `obdh.time_ref` (0x0A13): 0 = NONE (never set since the last
> bootloader reset --- the clock is still near J2000), 1 = GROUND, 2 = GPS
> ```
> FR:
> ```
> ### Étape 1 --- Lire l'horloge de bord et sa référence de temps
> **LABEL:** `STEP-1`
> **TC:** `REQUEST_TIME` (Service 9, Subtype 2) --- rapport de temps TM(9,2) explicite
> **Verify:** `obdh.mode == 0` (0x0300, timeout 10 s) --- NOMINAL
> **Note:** Consigner `obdh.time_ref` (0x0A13) : 0 = NONE (jamais réglée depuis la dernière
> réinitialisation du chargeur d'amorçage --- l'horloge est encore proche de J2000), 1 = GROUND, 2 = GPS
> ```
> (Keys, backtick spans, `Service 9, Subtype 2`, `timeout 10 s`, enum values unchanged; space before « : » added only in French prose after the key.)

**4. Procedure prerequisite with an operator value**
> EN: `- [ ] No imaging session in progress: \`payload.mode\` (0x0600) != 2`
> FR: `- [ ] Aucune séance de prise de vue en cours : \`payload.mode\` (0x0600) != 2`

**5. Textbook paragraph with mathematics — ch. 7**
> EN: `> **Sun-synchronous inclination** ($J_2$-driven RAAN precession of 360° per year; Part V §V.4):`
> `> where $\dot{\Omega}_{\text{req}} = \dfrac{2\pi}{365.25 \times 86\,400} = 1.991 \times 10^{-7}$ rad/s.`
> FR: `> **Inclinaison héliosynchrone** (précession de la RAAN due au $J_2$ de 360° par an ; partie V, §V.4) :`
> `> où $\dot{\Omega}_{\text{req}} = \dfrac{2\pi}{365.25 \times 86\,400} = 1.991 \times 10^{-7}$ rad/s.`
> (Math untouched, `\text{req}` kept; « where » → « où » because it is outside the math.)

**6. Table row — ch. 15 risk sources**
> EN: `| **Schedule** | Component delivery delay, test facility unavailable, regulatory delay |`
> FR: `| **Délais** | Retard de livraison d'un composant, moyen d'essai indisponible, retard réglementaire |`

**7. Figure caption with numbers for reading — ch. 11**
> EN: `**Figure 11.5** — Link-budget waterfall for the §11.8.1 S-band downlink (2 W transmitter, 6 dBi patch, 2.25 GHz over the 1695 km slant range at 10° elevation, 3 m ground dish at 150 K). … the dashed line is the received $C/N_0$ of 83.4 dBHz …`
> FR: `**Figure 11.5** — Bilan de liaison en cascade de la liaison descendante en bande S du §11.8.1 (émetteur de 2 W, antenne patch de 6 dBi, 2,25 GHz sur une distance oblique de 1695 km à 10° d'élévation, parabole sol de 3 m à 150 K). … la ligne tiretée indique le $C/N_0$ reçu de 83,4 dBHz …`

**8. Alt text and heading with attribute**
> EN: `![S-band downlink link-budget waterfall.](../assets/figures/fig_link_budget.png)` · `# Part 2 — CubeSat Operations {: .part-divider}`
> FR: `![Bilan de liaison en cascade de la liaison descendante en bande S.](../assets/figures/fig_link_budget.png)` · `# Partie 2 — Opérations d'un CubeSat {: .part-divider}`

**9. Callout box — ch. 17**
> EN: `> **Recommended background.** ECSS-E-ST-70C (Ground systems and operations); CCSDS 133.0-B (Space Packet Protocol); … This chapter builds on the link budget and ground-station types of Chapter 11 (§11.7–§11.9) …`
> FR: `> **Lectures préalables conseillées.** ECSS-E-ST-70C (*Ground systems and operations*) ; CCSDS 133.0-B (*Space Packet Protocol*) ; … Ce chapitre s'appuie sur le bilan de liaison et les types de stations sol du chapitre 11 (§11.7–§11.9) …`

**10. Voice-loop drill — ops book §9.2**
> EN: `- "FD, EPS — eclipse-entry T+04:12, SoC at exit 78%."` · `Score cross-talk and missed addressing.`
> FR: `- « FD, EPS — eclipse-entry T+04:12, SoC at exit 78%. »` · `Notez les interférences de parole et les appels mal adressés.`
> (Spoken callout kept verbatim inside French guillemets; narrative translated.)

**11. Facilitator book front matter**
> EN: `2. **Per-role background briefings** — a single chapter giving every CDF position the decisions, formulas, charts, pitfalls, and references they need from Day 1.`
> FR: `2. **Fiches de rôle** — un chapitre unique qui donne à chaque poste du CDF les décisions, formules, abaques, écueils et références dont il a besoin dès le jour 1.`

**12. Config YAML description (`commands/tc_catalog.yaml`)**
> EN: `description: "Control battery heater (device 0x0100)"` · `{ name: state, type: uint8, description: "0=OFF, 1=ON" }`
> FR: `description: "Commander le réchauffeur de batterie (équipement 0x0100)"` · `{ name: state, type: uint8, description: "0=OFF, 1=ON" }` (enum text unchanged)

---

## 19. QA checklist for every translated file

1. `grep` the English source and the French file for backtick spans and fenced blocks: counts and contents identical.
2. Procedures: run `pytest tests/test_content` and the procedure extraction audit; zero new problems; no French « étape N » jump verbs.
3. No `...`, no `"` used as quotation marks in prose, no space-less `?`/`!`/`;`/`:`, no point médian.
4. Every glossary-term occurrence uses the glossary rendering; no English left in prose except DNT items and callouts.
5. Numbers: decimal comma in prose and reading tables; point inside backticks, code, math, procedure annotations.
6. Headings sentence case; capital accents present; figure/table numbering unchanged.
7. Markdown builds (pandoc/mkdocs) with no new warnings; SVG labels fit.

---

## 20. Harmonisation rulings (packet G1, 2026-10-28)

Cross-packet decisions; the full decision table with replacement counts is `HARMONISATION.md` in this folder.
- **Procedure titles**: one canonical French title per procedure ID (`HARMONISATION.md` §1). « AOCS » in a title is prose, so it is written « SCAO » (COM-003/004/005, CTG-002/025/026/027); the console position and identifiers stay AOCS.
- **Control-room positions** (console display names): Direction de vol (the person: directeur de vol), Puissance et thermique, Dynamique du vol, Opérations charge utile, FDIR / Systèmes, TT&C, Propulsion. CDF positions: Analyste de mission, Ingénieur télécommunications.
- **Screen labels cited in books**: if the label exists in a French UI catalog (SMO `fr.json` / overlay, SpaceCDF `locales/fr*.json`), write the French catalog label followed by the English label in parentheses at its first mention in each chapter — « Lancer l'analyse » (Run Analysis) — and the French label alone afterwards. If it has no catalog entry, keep the English label exactly as the screen shows it (a French gloss may follow once). Inside parentheses use brackets: (« Puissance et thermique » [Power & Thermal]).
- **Books and running heads**: course textbook = « Manuel du cours » (title « SpaceCDF — Manuel du cours de conception concourante d'engins spatiaux », running head « SpaceCDF — Manuel du cours », footer-fr « Manuel du cours SpaceCDF · 2026 »); « Guide de l'animateur », « Guide de l'enseignant », « Cahier d'exercices du cours ». Position-reference appendices and OER Part IV: « Guide de référence des postes d'ingénierie / d'opérations » (« référentiel » stays reserved for baseline).
- **breakpoint** (simulator state) → « point de reprise » (instructor-console catalog). « point d'arrêt » is a QRH pause point.
- **Currency**, the same in every book: euros « k€ / M€ / € » (never kEUR / MEUR / EUR after a number); dollars « k$ / M$ / G$ », with « $ CA » / « $ US » only when the source states the currency. Where two `$` would fall on one prose line, escape them (`k\$`) so that pandoc does not read a maths span.
- **Status colours** in SpaceCDF and the books: vert / orange / rouge (amber → orange). MCS alarm colours remain vert / jaune / rouge (§14).

