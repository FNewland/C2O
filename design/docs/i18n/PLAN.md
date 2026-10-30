# Bilingual EN/FR — SMO suite, SpaceCDF and all course materials

*Plan of record, 2026-10-28. Owner: Franz Newland. Source language: English. Target: international/European French.*

## Owner rulings (2026-10-28)
| # | Ruling |
|---|---|
| R1 | **Modern UIs only.** Classic UIs stay English and byte-frozen (sha256 gate untouched). |
| R2 | **Identifiers stay English** (mnemonics, parameter IDs, enum/mode names, PUS service IDs, APIDs, procedure IDs, call-signs). Labels, descriptions and tooltips are translated. |
| R3 | **Translate both textbooks**: the facilitator book and the OER *Concurrent Spacecraft Design*. The OER French edition reuses the facilitator translation where text matches. |
| R4 | **International/European French.** Terminology follows ESA, CNES, FranceTerme and ITU-R, per `glossary.csv` and `STYLE_FR.md`. |
| R5 (proposed) | Engineering values on consoles keep the **decimal point** in French (operators type them back into command fields, where the comma is the argument separator). Prose uses the decimal comma. |
| R6 (proposed) | Voice-loop phraseology stays English (Go/No-Go, Standby, Hold, Mark), as in aviation, so mixed crews say the same words. |

## Source of truth
* Course books: Google Drive `SpaceCDF/docs/course/*.md`, the 2026-08-21 versions. These are newer than the copies in `~/SpaceCDF-arcadia/docs/course`.
* OER: `~/SpaceCDF-arcadia/docs/oer/chapters`.
* SMO: `~/SpaceMissionSimulation` (branch `evolution/2026-08`, with uncommitted work, which is left untouched).

## Where French lives
| English | French |
|---|---|
| Drive `docs/course/<book>.md` | Drive `docs/course/fr/<book>.md` |
| `cdf/docs/oer/chapters/NN_x.md` | `cdf/docs/oer/fr/chapters/NN_x.md` (built by `build_oer.py --lang fr`) |
| `cdf/docs/orbit_north/week3/*.md`, other cdf docs | `…/fr/<same name>.md` next to the source |
| `smo/configs/eosat1/procedures/**.md` | `smo/configs/eosat1/i18n/fr/procedures/**.md`. **Not** under `procedures/`, because the MCS loads `procedures/**/*.md` recursively. |
| `smo/configs/eosat1/manual/*.md` | `smo/configs/eosat1/i18n/fr/manual/*.md` (`09_command_reference` is generated from the YAML overlay, not hand-translated) |
| YAML labels/descriptions (tm, tc, events, fdir, monitoring…) | `smo/configs/eosat1/i18n/fr/db.yaml`: an overlay keyed by `kind:id:field`, each entry carrying its English hash |
| SMO modern UI strings | `smo_common/ui/i18n/fr.json` (shared) plus one `fr.json` per app. Keys are the English text, so English rendering is byte-identical. |
| SpaceCDF UI strings | `frontend/src/i18n/locales/{en,fr}.json` (react-i18next) |
| SMO operator docs (`docs/OPERATIONS_GUIDE.md` …) | `docs/fr/*.md` |

## How operators choose a language
Each browser chooses its own language, so two people in the same control room can run different languages. An **EN | FR** toggle in each modern UI's top bar saves the choice to `localStorage`. `?lang=fr` overrides it, which is useful for the wall display. The server default comes from `SMO_LANG` or `ui_lang:` in `mission.yaml`, and falls back to English. API traffic stays English and ID-based, and each client translates by ID. This keeps the spacecraft-agnostic ground tools and all existing parsers unchanged. Procedures and the manual are served in French through `?lang=fr` on the existing endpoints, so no new routes are added and the route-snapshot tests are unaffected. SpaceCDF has the same toggle, and its AI design agents receive the user's language and write French directly.

## Keeping EN and FR in sync: one tool, `i18n`
A stdlib-only Python CLI at `tools/i18n/` in each repo (the SMO copy is canonical; CDF carries a version-pinned copy). It handles all three kinds of content:

| Content | Unit | State |
|---|---|---|
| Markdown books/docs | section (each heading) | sidecar `fr/.i18n/<file>.json`: `{section_id: {en_hash, fr_hash}}` |
| UI catalogs | string (key = English text) | absent / orphaned keys |
| YAML overlay | field | `en_hash` stored inside each overlay entry |

Commands:
* `i18n status`: a table of files and sections marked **ok / stale** (English changed) / **fr-edited** (French changed by hand, offered for back-port) / **conflict** / **missing** / **orphan**. No AI involved.
* `i18n check`: structural parity (headings, code, maths, `code` spans, links, attribute blocks, tables, numbers), catalog key and placeholder parity, and identifiers preserved. Breakage fails; stale content only warns (`--strict` makes it fail). Runs as a git pre-commit hook and a pytest test.
* `i18n translate --stale`: collects only the stale sections or strings, together with the old English, new English, current French and the glossary terms that occur, and either calls Claude (if `ANTHROPIC_API_KEY` is set) or writes a work bundle for a Claude session. It asks for the smallest change to the existing French, so reviewed wording survives.
* `i18n apply` / `i18n accept`: write results and record hashes once reviewed.
* `i18n extract`: refreshes the YAML overlay and UI catalogs from the source (new keys come in as untranslated).

Day-to-day workflow: edit English as usual → the pre-commit hook says "3 sections stale in ch10" → run `i18n translate --stale` (or ask Claude to "sync the French") → review the diff → commit. A Claude skill, `bilingual-sync`, will encapsulate this.

## Work packets
**Wave 1**, in parallel:
* Infrastructure:
  * T0: sync tool
  * S0: SMO i18n runtime, toggle and Node-harness fix
  * C0: SpaceCDF react-i18next, language store and AI language plumbing
* Books:
  * F1–F5: facilitator book, about 99k words
  * O1–O5: ops book, about 86k words
  * W1: learner workbook
  * W2: ops workbook, instructor book, back cover and Week 3 pack

**Wave 2**, after S0/C0/T0:
* S1–S4: MCS, MCS shell + RF, planner + wall, instructor
* C1–C4: SpaceCDF live views only (92 of 144 files are dead code and are skipped)
* Y1: YAML overlay (about 2,600 strings)
* P1–P3: SMO procedures, about 92k words
* M1–M2: spacecraft manual
* D1: SMO operator docs
* D2: SpaceCDF docs

**Wave 3**, after F1–F5:
* OER1–OER5: about 150k words, reusing the facilitator French
* French PDF builds

**Wave 4: verification.** Full suites against the baseline (the SMO UI tests already show 12 failures and 5 errors on the untouched tree), French screenshots at four sizes, parity check on every file, an independent bilingual review agent spot-checking about 5 % of segments plus every procedure card, and a func_id/mnemonic audit of the French workbooks (the standing rule: workbooks get a func_id audit every batch).

## Delivery
All work happens on copies in the cloud workspace. It is delivered as tarballs to `_xfer/i18n/` plus a patch per repo, applied without touching existing uncommitted files. Franz commits on branch `i18n-fr`; the mount refuses git lock files. French course books are written to Drive `docs/course/fr/`.
