# i18n — keep the French in step with the English

Stdlib-only Python 3.10+ (PyYAML needed only for `extract` of the YAML overlay). Run from the repo root:
`python3 -m tools.i18n <cmd>` (or `python3 tools/i18n/cli.py <cmd>`; `--config PATH` for another `i18n.yaml`).
English is the source; nothing here ever edits English files.

## Maintainer workflow
1. Edit English as usual (docs, procedures, UI `t("…")` strings, YAML descriptions).
2. Commit: the pre-commit hook runs `check` on what you staged — broken structure blocks, stale French only warns.
3. `python3 -m tools.i18n status` — what is stale / missing / hand-edited, per file and section.
4. `python3 -m tools.i18n extract` — after YAML or UI-string changes: refresh `db.yaml` and catalog skeletons.
5. `python3 -m tools.i18n translate --stale` — writes a work bundle to `tools/i18n/work/` (git-ignored) (old EN, new EN, current FR, matching glossary rows).
6. In Claude Code: "process tools/i18n/work/INSTRUCTIONS.md" (or add `--api` with `ANTHROPIC_API_KEY` set to do it directly).
7. `python3 -m tools.i18n apply tools/i18n/work` — splices results in, applies French typography, records hashes, re-checks.
8. Review `git diff` of the `fr/` files, then `python3 -m tools.i18n build` (overlay → client JSON), commit.
9. Someone fixed French directly? `status` shows **fr-edited**; `backport` shows the diff; then `accept PATH`.
10. New pair whose French already exists: `accept --init` once (records today's hashes as the baseline).

Install the hook once: `ln -sf ../../tools/i18n/pre-commit .git/hooks/pre-commit`.

## Commands
| Command | Does |
|---|---|
| `status [--json] [--sections] [FILES]` | Per doc: section counts **ok / stale** (EN changed) / **fr-edited** / **conflict** (both) / **missing** / **orphan** (EN section gone) / **untracked** (FR never accepted); "structure changed" when EN headings moved (realigned by id). Catalog and overlay totals; unavailable roots (e.g. Drive not mounted). |
| `check [--strict] [--staged \| --files F…] [-v]` | **Errors:** per-section parity (code, maths, `code` spans, links, attribute blocks, comments, tables, numbers — via `mdparity`), lost mnemonics (`[A-Z][A-Z0-9_]{2,}` with a digit/underscore), forbidden FR wording (procedures' step-jumps), catalog placeholder mismatch, FR keys not used in sources, nested catalogs. **Warnings:** stale/missing/untracked sections, untranslated keys, stale overlay entries (errors with `--strict`). Exit 1 on errors. |
| `extract [--only overlay,catalogs] [--create] [--prune]` | Rebuild `configs/eosat1/i18n/fr/db.yaml` from the YAML rules in `i18n.yaml` (new keys `fr: null`; changed EN keeps the French, sets `en_prev`, becomes stale; removed keys kept as `orphan` if translated). Add missing catalog keys as `null` (existing files only unless `--create`). |
| `translate --stale [--emit DIR] [--api] [--model M] [--only docs,catalogs,overlay] [--include-conflicts] [--max-items N] [PATHS]` | Bundle of stale + missing items. Docs: `docs/<id>.en.md`, `.en_old.md` (from git, when recoverable), `.fr_current.md`, `.glossary.txt`; translator writes `docs/<id>.fr.md`. Strings: fill `"fr"` in `strings.json`. Minimal-edit instruction for stale items. |
| `apply DIR` | Validates (EN/FR unchanged since the bundle, one heading of the right level), typography-fixes, writes, updates the sidecar, runs `check` on touched files. |
| `accept [--init] [--waive] [--key K] [PATH[#section-id] …]` | Record current hashes as synced (after review). `--init` only onboards pairs without a sidecar; `--waive` records today's parity findings as accepted (e.g. `9:00` → `9 h 00`). With no path: everything, incl. the overlay. |
| `backport [PATHS]` | fr-edited/conflict sections with a diff (FR at last sync from git → now) and the current EN. |
| `build [--out F]` | Overlay → `smo_common/ui/i18n/fr.db.json` (`{key: fr}`, translated and non-stale only). |
| `typo FILE… [--fix]` | French spacing: U+202F before `; ! ?` and inside « », U+00A0 before `:`; never in code, maths, URLs, HTML, `{: attrs}`, `{{vars}}`, front matter, or `**TC:**`-style procedure keys. |

## Files and conventions
* **Docs**: section = heading + body to the next heading; preamble = section 0. Id = slug path of headings (`power/budget`, `~2` for duplicates, `{#id}` wins). FR mirrors EN headings 1:1. State: `<fr dir>/.i18n/<file>.json` (`en_hash`/`fr_hash` per section, sha256 of whitespace-normalised text, so rewrapping is not a change). Commit sidecars.
* **Catalogs** (i18next v4, flat, `keySeparator:false`): key = exact English; `{{var}}`; plurals `key_one`/`key_other` (`_many` optional); context `key_ctx`; `null`/`""` = untranslated. Expected keys come from `t()/tText()/tHtml()` calls, `data-i18n*` attributes and `i18nKey=` in the configured sources.
* **Overlay**: `db.yaml` entries `{key: "kind:id:field", en, en_hash, fr}`; clients look up `tdb("tc:AOCS_SET_MODE:description", en)`.
* Glossary `tools/i18n/glossary.csv`, style `tools/i18n/STYLE_FR.md` (rows matching each item go into the bundle).
* CDF carries a copy of this package (`cdf/tools/i18n/`); the SMO copy is canonical — copy it over when it changes.
