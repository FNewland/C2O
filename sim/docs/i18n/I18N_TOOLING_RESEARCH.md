# EN → FR internationalisation and sync tooling: research and recommendation

*Prepared 2026-10-28. Scope: the SMO suite (vanilla JS + Python), SpaceCDF (React 19/Vite/TS + FastAPI) and the Markdown teaching texts (~500k words). English is the source language and French (France/international) the target. Claude does the translation, and there is one maintainer with no SaaS budget.*

Each section separates what I **verified** (with a URL) from what comes **from prior knowledge, not re-verified this session**. The Section 9 list collects everything I could not verify.

---

## 0. Bottom line

1. **Write one small in-house tool, `i18n` (a Python CLI of roughly 1–1.5k lines), and use off-the-shelf libraries only for runtime rendering.** No open-source or free tool meets all four needs: (a) hash-based staleness per segment, (b) the same mechanism for UI catalogs, YAML labels and Markdown books, (c) LLM retranslation of only the stale parts with a glossary, and (d) detecting French that was edited directly. The closest prior art is **QuantEcon `action-translation`**, which uses Claude, lecture notes, section-level sync, heading maps, a "backward" drift review and a French glossary. It is GitHub-Action and MyST-centric and works across repositories. The idea is to copy its design, not adopt it as-is.
2. **SMO (vanilla JS):** keep a hand-rolled catalog, about 150 lines in `/static/shared/i18n.js`, using **i18next-compatible JSON v4**, `data-i18n` attributes, `Intl.PluralRules` and `Intl.NumberFormat`. Store the language choice per browser. The server sends **codes + args**, never English sentences, so two operators can see the same event in different languages. Engineering values keep the **decimal point**.
3. **SpaceCDF (React):** use **react-i18next + i18next-cli** (extract / sync / types / lint / status) and **eslint-plugin-i18next**. They use the same JSON catalog format as SMO, so one sync tool covers both. LLM design agents are told the user's locale and write natively in it. Their output is not machine-translated afterwards.
4. **Teaching texts:** keep a parallel `fr/` Markdown tree of complete files that people can edit and that the existing WeasyPrint build can compile. Add a sidecar state file per chapter with **per-section source and target hashes**. **Section** (heading with an explicit `{#id}`) is the unit for alignment and retranslation, and **block** hashes inside a section say *which* paragraphs changed. Retranslation is **diff-aware**: Claude gets old EN, new EN, current FR and the matching glossary terms, and makes the smallest edit to FR that reflects the change. Reviewed French wording therefore survives.
5. **Do not adopt** po4a, mdpo, Weblate or Lingo.dev as the backbone. Reasons are in Section 4.

---

## 1. Vanilla-JS runtime i18n with no build step (SMO)

### 1.1 Options

| Option | Maturity / status | Licence | No-build fit | Notes |
|---|---|---|---|---|
| **i18next** (core) | Very mature, started 2011. v25.x→**v26.0** removed legacy `interpolation.format` and `initImmediate` ([release notes](https://newreleases.io/project/npm/i18next/release/26.0.0)). | MIT | Medium. The package exports `dist/esm/i18next.js` and CJS, and a UMD build is copied to the package root at build time ([package.json](https://cdn.jsdelivr.net/npm/i18next@25.8.16/package.json)). The ESM build lists `@babel/runtime` as a dependency, so a bare browser `import` probably needs an import map or the vendored UMD `i18next.min.js` (not tested). | Large feature set: namespaces, plurals through `Intl.PluralRules`, a formatter, change events. More than SMO needs, but the **JSON v4 format is a de facto standard** that i18next-cli, Weblate and others can read. |
| **Fluent** (`@fluent/dom` + `@fluent/bundle`) | Mozilla. `@fluent/dom` **0.10.2**, about 8k downloads per week ([npm](https://www.npmjs.com/package/@fluent/dom)). | Apache-2.0 | Good (ES modules). `DOMLocalization` translates elements with `data-l10n-id` and uses a `MutationObserver`. | The best *language design* (asymmetric localisation, where French can add plural/gender variants that English does not have). Small ecosystem, slow releases, and its `.ftl` format has no counterpart in React/i18next tooling, so there would be two formats to keep in sync. |
| **FormatJS `intl-messageformat`** (ICU MF1) | Mature, community-maintained. react-intl is about 20 KB gzipped ([Tolgee 2026](https://tolgee.io/blog/react-i18n-libraries-comparison)). | BSD-3 | OK through an ESM CDN build or a vendored copy. | Good choice if ICU syntax is wanted everywhere. Its parser makes it heavier than needed. |
| **messageformat v4** (Unicode MF2) | MF2 is "Final Candidate" (March 2025). **TC39 `Intl.MessageFormat` is still Stage 1 (Oct 2026)** ([locize](https://www.locize.com/blog/messageformat-2-i18next), [TC39](https://github.com/tc39/proposal-intl-messageformat)). | Apache-2.0 | OK | Too early. Very little tooling uses it. |
| **Hand-rolled JSON + `data-i18n`** | Not applicable | Own code | **Best**: no dependency, about 150 lines | Covers everything SMO actually needs with the platform `Intl.*` APIs: lookup, `{{var}}` interpolation, `_one/_many/_other` plural suffixes chosen through `Intl.PluralRules`, `Intl.NumberFormat` / `DateTimeFormat`, and switching language at runtime. |

**Recommendation for SMO:** write the catalog code by hand but **use i18next's JSON v4 conventions** (`key_one`, `key_other`, `{{name}}` placeholders, `ns:key`). Then i18next-cli `status`/`sync`, Weblate's i18next format and the shared `i18n check` all understand the files. Moving to real i18next later would be a drop-in change. Python (Section 3) reads the same files with about 30 lines of code.

### 1.2 Sketch of `/static/shared/i18n.js` (ES module, no build)

```js
// /static/shared/i18n.js
const state = { lang: 'en', cat: {}, fallback: {}, listeners: new Set() };
const LS_KEY = 'smo.lang';

export async function initI18n(ns, { defaultLang } = {}) {
  const url = new URL(location.href);
  state.lang = url.searchParams.get('lang')                // wall display: ?lang=fr
            || safeGet(LS_KEY)                             // per-browser choice
            || (navigator.language || 'en').slice(0, 2);   // Accept-Language-ish
  if (!['en', 'fr'].includes(state.lang)) state.lang = defaultLang || 'en';
  state.fallback = await load('en', ns);
  state.cat = state.lang === 'en' ? state.fallback : await load(state.lang, ns);
  document.documentElement.lang = state.lang;
  applyI18n(document);
}
export async function setLang(lang, ns) { safeSet(LS_KEY, lang); await initI18n(ns); state.listeners.forEach(f => f(lang)); }
export const onLangChange = f => state.listeners.add(f);

export function t(key, args = {}) {
  let k = key;
  if (typeof args.count === 'number') {
    const cat = new Intl.PluralRules(state.lang).select(args.count); // fr: one | many | other
    if (lookup(`${key}_${cat}`) != null) k = `${key}_${cat}`;
    else if (lookup(`${key}_other`) != null) k = `${key}_other`;
  }
  const s = lookup(k) ?? key;                       // show the key, never an empty string
  return s.replace(/\{\{(\w+)\}\}/g, (_, v) => args[v] ?? `{{${v}}}`);
}
export function applyI18n(root) {                   // call after every innerHTML render
  root.querySelectorAll('[data-i18n]').forEach(el => el.textContent = t(el.dataset.i18n));
  root.querySelectorAll('[data-i18n-attr]').forEach(el =>   // "title:mcs.tip.ack;aria-label:mcs.ack"
    el.dataset.i18nAttr.split(';').forEach(p => { const [a, k] = p.split(':'); el.setAttribute(a, t(k)); }));
}
// number formatting: see 1.3
```

**Template literals and `innerHTML`.** mcs.js builds most of its UI this way. Change `` `<th>Value</th>` `` to `` `<th>${t('mcs.col.value')}</th>` ``. Because every render reads `t()` at render time, switching language is just `setLang()` followed by a re-render, with no page reload. Any values put into HTML must still be escaped: a French translation could contain `<`.

**Several operators in one control room:** the language belongs to the **browser** (localStorage plus an optional `?lang=` that overrides it for wall displays and kiosks), never the server. For this to work, **every server-originated message must be structured**:

```json
{"type":"event","code":"EVT_BATT_UNDERVOLT","sev":"HIGH","args":{"param":"EPS_BAT_V","value":6.42,"limit":6.5,"unit":"V"}}
```

Each browser then renders `t('evt.EVT_BATT_UNDERVOLT', args)` in its own language. Where the server currently sends English prose (error strings, PUS failure reasons, instructor-console messages), keep an English `text` field as a fallback during migration and add `code` and `args`. The `i18n check` step can warn when the shared JSON message schema has a `text` field but no `code`.

### 1.3 French numbers, units and punctuation, and the telemetry exception

*Verified:* in CLDR 34 (2018), the French group separator changed from U+00A0 to U+202F, the narrow no-break space ([Unicode list](https://www.unicode.org/mail-arch/unicode-ml/y2018-m09/0069.html)). `Intl.NumberFormat('fr-FR')` in current browsers therefore prints `12 345,6` with U+202F and a decimal comma. Babel 2.18 ships CLDR 47 ([pkgsrc](https://mail-index.netbsd.org/pkgsrc-changes/2026/02/02/msg339599.html)).

*From prior knowledge (standard French typography: Imprimerie nationale, Debian FR guide [link](https://www.debian.org/international/french/typographie)):* in **France**, a narrow no-break space (U+202F) goes before `; ! ?`, inside `« »`, before `%` and between a number and its unit. Before `:` a full no-break space (U+00A0) is traditional, and U+202F is common. **Canadian (OQLF) usage is different**: no space before `; ! ?`. Because European French is the target, apply France rules. **Do this with a deterministic post-processor in the `i18n` tool, not by trusting the LLM.**

**`Intl.PluralRules('fr')` returns `one`, `many` and `other`.** The `many` category was added to French in recent CLDR versions for large round numbers ("1 million **de** …"); this is from prior knowledge and not re-checked. Catalogs should define `_one` and `_other` and treat `_many` as optional. The parity check must not report a French `_many` key as "extra".

**Telemetry and engineering values: keep the decimal point.** Recommendation:
- **Engineering values keep EN formatting in both languages**, with `.` as decimal and no thousands grouping. This covers parameter values, limits, calibrated and raw values, command arguments, input fields, hex/raw dumps, the PUS packet viewer and timestamps (ISO 8601/CUC). Reasons:
  - procedures, the spacecraft database, logs and exported CSVs are written with `.`;
  - an operator who copies a value into a telecommand field must not run into locale parsing;
  - mixed-language crews in one room must see identical numbers.

  The SI Brochure (BIPM, 9th ed.) and ISO 80000-1 allow **either** a point or a comma as the decimal marker. Using a point is therefore not "wrong French" (prior knowledge, not re-verified).
- **Prose and labels** (help text, dialog sentences, instructor narrative) use French formatting.
- Provide `fmtEng(v, digits)` (always `.`) and `fmtNum(v)` (locale) in `i18n.js`. Lint mcs.js for `toLocaleString` in telemetry code paths. An optional per-user setting "Number style: engineering / locale" defaulting to engineering costs little.
- **Could not verify** what ESA/ESOC (SCOS-2000), CNES or EUMETSAT ground systems do. I found no public statement that their MCS consoles localise number formats. SCOS-2000 documentation and ESA operations material are in English, and European multinational operations generally run their consoles in English (prior knowledge). The proposed policy is consistent with that, but it should not be cited as ESA practice without a source.

---

## 2. React (SpaceCDF)

### 2.1 Comparison (2026 status)

| Library | Status (verified) | Message format | Extraction | TS key safety | Fit here |
|---|---|---|---|---|---|
| **react-i18next** + **i18next-cli** | i18next is the most widely used option ([Tolgee, Jul 2026](https://tolgee.io/blog/react-i18n-libraries-comparison)). **i18next-cli** (Sept 2025, SWC-based) has `extract`, `sync`, `types`, `lint` and `status` commands, plus `migrate-config` to move off i18next-parser ([dev.to](https://dev.to/adrai/supercharge-your-i18next-workflow-with-the-all-new-i18next-cli-341p)). | JSON v4 (ICU through a plugin) | `i18next-cli extract` | `i18next-cli types` generates typed keys | **Best fit.** Same catalog format as SMO, and the `status`/`lint` commands overlap with the CI checks. |
| **Lingui** | **Lingui 6.0 (22 April 2026):** ESM-only, Node ≥22.19, Vite 8 plugin, named placeholders through the `ph()` macro, smaller install ([announcement](https://js-lingui-2fbw45h8a-crowdin.vercel.app/blog/2026/04/22/announcing-lingui-6.0)). Maintained by Crowdin since 2022. | ICU in **PO** files, with the source string as the key | `lingui extract` / `compile` | Compile-time checks | Very good DX and the smallest runtime, but it uses PO and source-as-key, a second catalog format different from SMO. Source-as-key also means every English wording fix changes the key. |
| **react-intl** (FormatJS) | Mature, about 20 KB gzipped, keys not type-checked by default (Tolgee). | ICU | `formatjs extract` | Weak | Workable, no advantage here. |
| **Paraglide JS 2** (inlang/opral) | MIT. **Compiler**: compiles messages into tree-shakable functions, "designed for Vite and modern ESM bundlers" ([README](https://unpkg.com/@inlang/paraglide-js@2.21.0/README.md)). | inlang JSON (plugins for i18next, ICU1, XLIFF) | Not needed, because messages are functions | Excellent (functions) | Good for Vite, but **needs a build step**, so it cannot serve SMO. Adopting it would mean two runtimes. |

**Linting for hard-coded strings:** **eslint-plugin-i18next 6.1.1**. It supports flat config (`i18next.configs['flat/recommended']`). Since v6, `no-literal-string` checks only JSX text by default ([npm](https://www.npmjs.com/package/eslint-plugin-i18next)). `i18next-cli lint` has its own hard-coded-string heuristic. Use the ESLint rule in the editor and in CI.

### 2.2 SpaceCDF recommendation
- Layout `frontend/src/locales/{en,fr}/{common,design,review,...}.json`, i18next JSON v4, namespaces per feature area.
- `i18next-cli extract` adds new keys to `en/*.json` (English values come from defaults in code, `t('k', 'Default text')`). `i18next-cli types` generates `i18next.d.ts`. `i18next-cli sync` aligns key sets. **Our `i18n` tool then handles French content, staleness and retranslation** (i18next-cli `status` reports missing keys but does not track whether the English text changed).
- Keep the language in Zustand and persist it to localStorage. Call `i18n.changeLanguage()` to switch. The `<html lang>` attribute must follow the language.
- **Backend LLM "design agents":** add `locale` to the agent request and say in the system prompt "Respond in {French (France)}. Keep identifiers, units, part numbers and requirement IDs unchanged. Use the attached glossary." Store the generated artefacts with a `lang` field. **Do not** generate English and machine-translate it afterwards: that costs twice as much and is worse. If a team needs both languages of a document, translate on demand through the same `i18n` glossary path.
- Backend validation or error messages: return `{code, params}` (FastAPI `HTTPException(detail={"code":..., "params":...})`) and let the frontend render them.

---

## 3. Python server-side strings and YAML-sourced labels

### 3.1 gettext/Babel or shared JSON?
- **Babel** (2.18, CLDR 47, BSD) is still the standard for gettext `.po` extraction and **CLDR-correct number/date formatting** in Python ([pkgsrc changelog](https://mail-index.netbsd.org/pkgsrc-changes/2026/02/02/msg339599.html)).
- **Recommendation: do not introduce gettext.** Server-side prose should be minimal, because the server sends codes. The few server-rendered strings (PDF reports, exported procedures, HTTP error fallbacks) should read the **same JSON catalogs** through a tiny `smo_shared.i18n.t(key, lang, **args)`. Gettext would mean a second format, a second extraction path and a second staleness mechanism.
- Use **Babel only for formatting** in server-generated documents (`babel.numbers.format_decimal(x, locale='fr_FR')`, dates) and for **Accept-Language negotiation** (`babel.Locale.negotiate(parsed_header_langs, ['en','fr'], sep='-')`, from prior knowledge). The negotiated value is only a *default*: the browser's explicit choice wins.

### 3.2 Localising YAML telemetry, telecommand, event and procedure metadata
Three patterns:

| Pattern | Pros | Cons |
|---|---|---|
| Parallel fields (`description_fr:`) in the same YAML | Easy to see while editing | Clutters the configs that drive the simulator, mixes translation concerns into the engineering database, and gives no natural place to record staleness. Every consumer has to choose the field. |
| Overlay files (`config/i18n/fr/telemetry.yaml` with the same structure) | Source stays clean, and the overlay can be merged at load time | A second tree to keep aligned with the first. |
| **Catalogs keyed by stable ID** (`tm.EPS_BAT_V.description`) **(recommended)** | Same format, tooling, checks and Claude path as the UI strings. Mnemonics are natural stable keys. The browser renders labels in each operator's language. | Needs an extraction step from YAML to catalog. |

**Recommended:** `i18n extract-yaml` reads the configured YAML fields and writes `locales/en/db.json` (generated, never edited by hand). French lives in `locales/fr/db.json`. The UI calls `t('db:tm.EPS_BAT_V.description')` and falls back to the English value the server already sends. **Mnemonics, parameter IDs, units, enum *raw* values and PUS service/subtype numbers are never translated.** Enum *display labels* are translated (`db:tm.AOCS_MODE.enum.SAFE` → "SURVIE" or kept as "SAFE"; this is a glossary decision, see Section 6).

The 69 procedures and the manual chapters are Markdown and go through the Markdown pipeline (Section 4). Their step **mnemonics and commands** are protected tokens.

---

## 4. Markdown and document translation sync (the critical part)

### 4.1 Requirements
- Edit EN, have FR follow, flag stale FR automatically, and let Claude retranslate only what changed.
- FR files are real Markdown that the **existing WeasyPrint scripts build unchanged** (`lang="fr"` for hyphenation).
- Content includes math (`$…$`, `$$…$$`, pandoc-ish), fenced code, pipe tables, kramdown/attr_list-style attributes such as `{: .part-divider}`, admonitions, footnotes, cross-references and mnemonics.
- Detect drift in **both** directions, including someone fixing FR directly.
- One maintainer: plain files plus git, no server.

### 4.2 Tools evaluated

| Tool | Status / licence (verified where cited) | How staleness works | Markdown fidelity | Verdict |
|---|---|---|---|---|
| **po4a** (Text module, `markdown` option) | Long-standing Debian tool (0.74 in Debian) ([source](https://sources.debian.org/src/po4a/0.74-1/lib/Locale/Po4a/Text.pm)). GPL. | gettext `msgmerge` marks changed paragraphs **fuzzy**: real per-paragraph staleness, battle-tested. | Paragraph-level, with YAML front-matter keys support. *From prior knowledge:* tables are handled as whole blocks, extended syntax (math, attribute lists, admonitions) is treated as plain text, and lines can get re-wrapped. I could not load the current man page to confirm this. | **Not recommended as backbone.** The FR `.md` is *generated* from the PO, so editing FR directly is lost or must happen in the PO. It is Perl, and the PO files would be huge for 500k words. |
| **mdpo** (md2po/po2md) | **v2.1.4, 22 Apr 2025, BSD-3, Python ≥3.8 and <3.14** ([PyPI](https://pypi.org/project/mdpo/)). | PO fuzzy flags | CommonMark plus some extensions. No math or attribute-list support documented. | Cleanest PO round-trip for Markdown, but it **excludes Python 3.14** and has the same "FR is generated" problem. |
| **Translate Toolkit md2po** / **Weblate** | Weblate's Markdown format (since 5.0) is in the 2026.11 docs ([docs](https://docs.weblate.org/en/latest/formats/markdown.html)). Weblate has an **Anthropic (Claude)** machine-translation backend since 5.16 ([docs](https://docs.weblate.org/fr/latest/admin/machine.html)). GPL. | Server-side translation memory plus "needs editing" states | Front matter is one block unless configured. Table row reordering can lose translations. **"Changes made in translated files are not imported"** (Weblate is the source of truth). No math support documented. | Weblate is excellent for teams, but for one person it means a self-hosted Django, Postgres and Redis stack, a web UI in the loop, and no direct FR edits. **Use only if volunteer translators appear later.** The JSON catalogs proposed here are Weblate-compatible, so that door stays open. |
| **Pontoon** (Mozilla) | Fluent/PO-centric server | Server | No Markdown focus | Not a fit. |
| **Crowdin / Lokalise / GitLocalize** | SaaS | Translation memory plus "outdated" flags | Good | Reference only. Their model (segment, TM, flag when the source segment changes, pre-translate with MT/LLM, review) is the pattern to copy locally. |
| **Lingo.dev** | The current CLI "ships your source content to a localization engine, which translates it server-side." The legacy `npx lingo.dev` flow called the LLM locally ([docs](https://lingo.dev/en/cli/fundamentals/i18n-lock-lockfile)). | Lockfile of fingerprints, so only new or changed keys are pushed | Supports Markdown | Good idea (lockfile of source fingerprints), but the platform is SaaS-oriented. **Copy the lockfile idea, not the tool.** |
| **GenAIScript continuous translation** (Microsoft, Jul 2025) | Script, MIT | **Per-mdast-node SHA-256** (position stripped), cached in `translations/<lang>.json`. Only uncached nodes go to the LLM. ([blog](https://microsoft.github.io/genaiscript/blog/continuous-translations)) | Translates only `text`, `paragraph`, `heading` and `yaml` nodes, so code is never touched. Wraps chunks in `┌T001┐…└T001┘` markers. Checks that output re-parses as Markdown and that links did not change. **LLM-as-judge** step that refuses to write poor output. | **Strong design reference** for the hashing, the markers and the validation gate. Node-level granularity loses context for prose and textbooks, and the FR file is regenerated from the cache, so direct FR edits are lost. |
| **QuantEcon `action-translation`** (v0.26.0, MIT) | Built for multilingual **lecture notes** (MyST Markdown, with math and code), using **Claude** (default `claude-sonnet-5`, `claude-opus-5-5` selectable). Per-language glossaries; **the French glossary has 369 terms** ([overview](https://quantecon.github.io/action-translation), [action reference](https://quantecon.github.io/action-translation/action-reference)). | Splits at `##` sections, compares old and new source and sends only changed sections in **UPDATE** mode, then merges them. Per-file state `.translate/state/<file>.yml` with `source-sha`, `synced-at`, model, mode and section count. `status` reports ALIGNED, OUTDATED, MISSING_HEADINGMAP and so on, without any LLM call ([CLI ref](https://quantecon.github.io/action-translation/cli-reference)). | **Heading map** in the target front matter maps EN heading paths (`A::B`) to FR headings for section alignment ([heading maps](https://quantecon.github.io/action-translation/heading-maps)). Preserves code, math, directives and cross-references. **`backward`** finds FR improvements worth porting back to EN. **`forward`** resyncs drifted copies. **`review`** adds an AI quality score. | **Closest existing match.** Drawbacks for this case: it is built around **source repo → separate target repo PRs** as a GitHub Action (a Node CLI also exists), it is MyST-specific, staleness is per file (commit SHA) rather than per section hash, and it has no notion of UI catalogs or YAML. **Borrow its design, or trial its CLI on one book before writing the Markdown half yourself.** |
| **mkdocs-static-i18n / Docusaurus i18n / Quarto (babelquarto)** | Site generators | None (they render parallel files) | Not applicable | Only useful as a **layout convention** (folder per language). They do not track staleness. Not relevant to the WeasyPrint pipeline. |
| **Sphinx-intl** | gettext workflow for Sphinx | PO fuzzy | reST | Not applicable (Markdown and WeasyPrint here). |

### 4.3 Which granularity?

| Granularity | Staleness precision | LLM context quality | Alignment robustness | Direct FR edits | Single-maintainer effort |
|---|---|---|---|---|---|
| File | Poor: one typo retranslates a chapter | Excellent | Trivial | Detectable, too coarse to act on | Lowest, but expensive and destroys reviewed FR |
| **Section (heading + `{#id}`)** | Good | **Excellent** (coherent argument, terms consistent within it) | **Robust with explicit IDs** | Detectable per section | **Low** |
| Paragraph / block | Excellent | Weak (loses context, terms drift between paragraphs) | Fragile when paragraphs are split or merged | Detectable but hard to match | Medium to high |
| Sentence (TM style) | Excellent | Poor | Very fragile (EN and FR sentence counts differ) | Effectively impossible | High |

**Recommended: a hybrid.**
- **The section is the unit for alignment and retranslation.** A section runs from one heading (any level) up to, but not including, the next heading.
- **Block hashes inside a section are kept for diagnosis only.** They let the tool tell Claude, and the report tell the user, *which* paragraph changed, and they keep the "minimal edit" prompt focused.
- **Give every heading an explicit, stable ID.** A one-time `i18n ids --write` adds `{#sec-power-budget}` from slugs to EN headings, and the same ID appears in FR. This also fixes cross-references in the French PDF, since anchors become language-independent. WeasyPrint/markdown with attr_list already supports `{#id}` and `{: .class}` (the existing `{: .part-divider}` shows the extension is enabled; verify heading-ID handling in the build scripts).
- **Very long sections** (more than about 1,200 words without subheadings) are split for translation at **block boundaries** into numbered chunks (`sec-x#c2`). Alignment within the section is then by block index, and the structure check enforces equal block counts.

### 4.4 Normalised hashing, so cosmetic edits don't mark FR stale
Before hashing:
- Turn soft line breaks into spaces, collapse whitespace and strip trailing spaces.
- Normalise Unicode to NFC.
- Ignore pure re-wrapping.

A whole-file reformat then does not mark the French stale. Use SHA-256 of the normalised text, truncated to 16 hex characters.

### 4.5 Detecting drift in both directions
The sidecar stores, for each section, `src_hash` (EN when last synced) and `tgt_hash` (FR when last synced or accepted).

| EN now vs `src_hash` | FR now vs `tgt_hash` | Status | Action |
|---|---|---|---|
| same | same | `OK` | none |
| **changed** | same | `STALE` | `i18n translate` (diff-aware update) |
| same | **changed** | `FR_EDITED` | Someone fixed the FR directly. `i18n accept` records the new `tgt_hash` after review. Optionally `i18n backport-review` asks Claude whether the FR change shows an EN error, as QuantEcon's `backward` does. |
| changed | changed | `CONFLICT` | Manual, or Claude with both diffs; never automatic |
| absent in FR | — | `MISSING` | translate |
| — | ID only in FR | `ORPHAN` | EN section deleted or renamed. Delete or remap. |

`src_commit` (the git SHA where EN was last synced) is stored too. That lets the tool recover the **old EN text** with `git show <sha>:path` and send Claude a real diff, not just the new text.

### 4.6 Diff-aware retranslation prompt (the key quality lever)
For each `STALE` section, send Claude:
1. `EN_OLD` (from git at `src_commit`), `EN_NEW`, `FR_CURRENT`
2. A unified diff of EN_OLD → EN_NEW, with the changed blocks marked
3. **Only the glossary entries whose EN term appears in EN_NEW** (Section 6), plus the do-not-translate list
4. Style rules: European French; *vous* in textbooks; France punctuation spacing is applied afterwards by the tool, so the model should not insert special spaces; keep `{#ids}`, `{: .classes}`, math, code, link URLs, footnote labels and mnemonics byte-identical; same block count and order.
5. Instruction: *"Update FR_CURRENT so it reflects the EN change. Edit only the affected sentences; preserve all other French wording exactly."* (For `MISSING` sections, use a fresh-translation prompt with the previous and next FR sections as context.)

Before the model sees the text, the tool **masks protected spans** using GenAIScript-style placeholders: math to `⟦M3⟧`, inline code to `⟦C1⟧`, attribute blocks to `⟦A2⟧`, URLs to `⟦U4⟧`. Afterwards it unmasks them and verifies that every placeholder came back exactly once. The model cannot damage `$\Delta v = I_{sp} g_0 \ln(m_0/m_f)$` if it never sees it as editable text.

**Where Claude runs.** The default for a single maintainer is **locally**, not in CI:
- **(a) Direct API:** `i18n translate --stale` calls the Anthropic API with `ANTHROPIC_API_KEY`.
- **(b) Claude Code packets:** `i18n translate --emit .i18n/work/` writes self-contained work packets (JSON plus instructions). A Claude Code session processes them, and `i18n apply .i18n/work/` validates and merges the results. Option (b) needs no API-key plumbing and fits his existing Claude Code workflow.

CI only ever runs `--check`. Results arrive as an ordinary git diff for (optional) human review. Commit messages can carry `i18n: retranslated 7 stale sections (ch03, ch07)`.

**Bulk first pass (~500k words).** Run it chapter by chapter with the same tool (every section is `MISSING`). If the API path is used, consider the API's batch mode, since latency does not matter. Check current pricing and batch terms before committing; I did not verify them for this report. Sending each section with the previous and next sections as read-only context improves coherence.

---

## 5. CI and pre-commit enforcement (`i18n check`)

| Check | UI catalogs | YAML-derived catalogs | Markdown |
|---|---|---|---|
| Key / section parity (missing, extra) | ✔ (allow FR-only `_many` plural forms) | ✔ | ✔ (by `{#id}`) |
| Placeholder set equality (`{{x}}`, `{0}`, ICU args, `<1>…</1>` Trans tags) | ✔ | ✔ | n/a |
| Protected tokens equal as multisets: inline code, math, URLs, `{#id}`, `{: …}`, footnote labels `[^n]`, image paths | — | — | ✔ |
| Mnemonics and identifiers preserved: regex `\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b`, `TC\(\d+,\d+\)`, `S\d+`, `0x[0-9A-F]+`, requirement IDs | ✔ | ✔ | ✔ |
| Numbers preserved, **normalised** (FR `3,3` ≡ EN `3.3`, FR `12 345` ≡ `12345`) | ✔ | ✔ | ✔ (prose only; math and code are already exact) |
| Units preserved (`V`, `W`, `dBW`, `km/s`, …) | ✔ | ✔ | ✔ |
| Structure: same heading levels; same block count per section (tables: same rows and columns) | — | — | ✔ |
| Staleness (`STALE`, `FR_EDITED`, `CONFLICT`) | ✔ | ✔ | ✔ |
| French typography (U+202F before `; ! ?`, inside « », before % and units) | fix with `--fix` | fix with `--fix` | fix with `--fix` |
| Front matter: FR has `lang: fr`, `title` translated | — | — | ✔ |

Policy: **missing, extra, placeholder and protected-token mismatches are errors. Stale content is a warning locally and an error on `main` only if `--strict`.** Otherwise a typo fix in EN would block commits until French is regenerated. The `status` report prints a short table per file.

**pre-commit** (`.pre-commit-config.yaml`):
```yaml
repos:
  - repo: local
    hooks:
      - id: i18n-check
        name: i18n check (parity, placeholders, protected tokens)
        entry: i18n check --fail-on=error --warn-on=stale
        language: system
        pass_filenames: false
        files: '(locales/.*\.json|.*\.md|configs/.*\.ya?ml)$'
```
In the React repo, add `i18next-cli lint` / ESLint `i18next/no-literal-string` and `i18next-cli types --check` (or a typecheck) alongside it.

---

## 6. Terminology (European French, space)

| Source | What it is | Access / format | Licence | Use |
|---|---|---|---|---|
| **FranceTerme** (Commission d'enrichissement, Journal officiel) | Official French recommended terms. Space terms carry the domain **"Spatiologie"** (e.g. *astronef* for *spacecraft*, JO 22 Sept 2000) ([record](https://www.culture.fr/franceterme/france_terme_rtf?num=SPAT29)). There is also a 2013 published *Vocabulaire des sciences et techniques spatiales* ([PDF](https://www.culture.gouv.fr/content/download/93742/file/voca_en_ligne_2013_spatial_def.pdf)). | Full base as **XML** (~8.5 MB) on data.gouv.fr, updated after each JO publication, last update 13 Mar 2026 ([dataset](https://www.data.gouv.fr/datasets/base-franceterme-termes-scientifiques-et-techniques-1)) | **Licence Ouverte / Etalab** (reusable) | **Primary normative source** for European French. Filter on domain `Spatiologie`. Note that FranceTerme recommends terms that industry does not always use (e.g. *astronef*, while CNES and ESA texts say *engin spatial / satellite*). Record "preferred in practice" separately. |
| **IATE** (EU interinstitutional termbase) | EN↔FR with reliability scores | **TBX (ISO 30042:2019) or CSV export**, filter by domain and language. Requires login; links expire after 7 days ([help](https://online-help.iate.europa.eu/technical-info/iate-download/)). | IATE reuse conditions (check them; not read in full) | Large secondary source. Take only entries with reliability ≥ 3 in the space/aerospace domains. |
| **ECSS glossary**: ECSS-S-ST-00-01C, adopted by CEN as **EN 16601-00-01:2015** | The authoritative definitions for ECSS terms ([iTeh](https://standards.iteh.ai/catalog/standards/cen/e83ab85e-b075-45e5-b16b-cea521fd0815/en-16601-00-01-2015)) | ECSS edition: English, free from ecss.nl. CEN ENs normally exist in EN/FR/DE, so a French NF EN 16601-00-01 (AFNOR) probably exists but is paid. **Not verified.** | Paid standard (CEN version) | Check key ECSS concepts (verification vs validation, *qualification*, *recette*…) if the user can get the AFNOR edition. |
| **TERMIUM Plus** (Government of Canada) | EN/FR, strong in aerospace | Web lookup | Free | **Secondary.** Marks Canadian vs France usage. Good for checking, but prefer FranceTerme/IATE where they differ. |
| **Translation Bureau, *International Space Station Glossary*** (Terminology Bulletin 255, 2004, ~760 concepts) | Bilingual EN/FR ([record](https://publications.gc.ca/site/eng/9.582465/publication.html)) | PDF | Crown copyright | Useful for ops vocabulary; Canadian origin. |
| **CNES / ESA** | No public, downloadable CNES or ESA EN-FR termbase found. | — | — | **Could not verify** that one exists publicly. CNES French publications serve as usage evidence. |
| **QuantEcon French glossary** (369 terms) | Economics and maths lecture terms ([overview](https://quantecon.github.io/action-translation)) | JSON in their repo (schema not documented on the pages read) | MIT | Possibly useful for general maths and pedagogy terms. |

**Project glossary format.** Use a CSV in git (easy to edit and diff), convertible to TBX-Basic if ever needed:

```csv
en,fr,type,dnt,note,source
telemetry,télémesure,n.f.,,,FranceTerme
telecommand,télécommande,n.f.,,,FranceTerme/IATE
ground segment,segment sol,n.m.,,,IATE
safe mode,mode survie,n.m.,,"UI enum label SAFE stays 'SAFE' in consoles",project
attitude and orbit control system (AOCS),système de contrôle d'attitude et d'orbite (SCAO),n.m.,,"acronym SCAO in prose; keep AOCS in mnemonics",project
link budget,bilan de liaison,n.m.,,,IATE
EO-Sat-1,EO-Sat-1,,yes,"proper name",project
PUS,PUS,,yes,"ECSS Packet Utilisation Standard; never translate",project
```

`dnt=yes` is a **do-not-translate** entry, also fed to the identifier-preservation check. When prompting, the tool selects **only entries whose `en` term (lemmatised or case-folded) appears in the segment**, so prompts stay short and the terminology constraint actually holds. This follows standard practice for LLM terminology control and the WMT 2025 terminology-task approaches ([example](https://arxiv.org/html/2510.17504v1)). An optional `i18n glossary audit` reports FR segments that contain an EN glossary term but not the required FR term.

**Acronym policy (decide once and record it in the glossary notes):** in prose, give the French form with the English acronym at first use, e.g. *système de contrôle d'attitude et d'orbite (SCAO, en anglais AOCS)*. In consoles and procedures, keep English mnemonics and acronyms, because operators read them aloud and they appear in the database.

---

## 7. Recommended architecture

### 7.1 One tool, `i18n` (Python ≥3.11, ~1–1.5k lines)
Dependencies: `markdown-it-py` (+ `mdit-py-plugins` for front matter, footnotes, dollarmath and attrs) for **segmentation only**, never for re-rendering, because we splice original text spans. Also `ruamel.yaml`, `anthropic` (optional), and `babel` (optional, for formatting). Ship it as its own small package, installed with pip in each repo, or vendored as `tools/i18n/`.

**Config per repo, `i18n.toml`:**
```toml
[project]
source = "en"
targets = ["fr"]
glossary = "i18n/glossary.csv"
state_dir = ".i18n/state"
typography = "fr-FR"          # France NNBSP rules applied by --fix / after translate

[protect]                     # extra regexes treated as untranslatable spans
patterns = ['\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b', 'TC\(\d+,\d+\)', '\bS\d{1,2}\b', '0x[0-9A-Fa-f]+']

[[catalogs]]                  # i18next JSON v4
src = "smo_shared/static/shared/locales/en/*.json"
tgt = "smo_shared/static/shared/locales/{lang}/{name}.json"

[[yaml]]                      # YAML → generated EN catalog
src = "configs/eosat1/{telemetry,telecommands,events}/*.yaml"
fields = ["label", "description", "enum_labels.*"]
key = "{kind}.{id}.{field}"
out = "smo_shared/static/shared/locales/{lang}/db.json"

[[markdown]]
src = "books/ops/en/**/*.md"
tgt = "books/ops/fr/{rel}"
unit = "section"
max_section_words = 1200
```

**Commands:**
```
i18n ids --write                 # one-off: add stable {#ids} to EN headings, mirror to FR
i18n extract-yaml                # regenerate locales/en/db.json from YAML
i18n status [--json] [PATH...]   # OK/STALE/FR_EDITED/CONFLICT/MISSING/ORPHAN table; no LLM
i18n check [--strict] [--fix]    # CI/pre-commit gate (Section 5); --fix applies FR typography
i18n translate --stale [PATH...] [--dry-run] [--model claude-opus-5-5] [--emit DIR | --api]
i18n apply DIR                   # merge Claude Code work packets, validate, update state
i18n accept PATH[#id] | KEY      # reviewed a direct FR edit → record tgt_hash
i18n backport-review [PATH...]   # LLM: do FR-only edits reveal EN errors?
i18n glossary audit
```

### 7.2 Sidecar state formats

**Markdown**: `.i18n/state/books/ops/ch03-power.md.fr.json`
```json
{
  "schema": 1,
  "source": "books/ops/en/ch03-power.md",
  "target": "books/ops/fr/ch03-power.md",
  "lang": "fr",
  "segmenter": "md-section-v1",
  "src_commit": "4e1c9a7",
  "sections": {
    "sec-power-budget": {
      "src_hash": "9f2c0b6d1a7e44c2",
      "tgt_hash": "41aa83e0c5d9b712",
      "blocks_src": ["c1d2e3f4a5b60718", "0a9b8c7d6e5f4a3b", "77e1f0c2d3b4a596"],
      "synced_at": "2026-10-28T14:02:11Z",
      "by": "claude-opus-5-5",
      "mode": "update",
      "reviewed": false
    },
    "sec-battery-dod": {
      "src_hash": "5b6c7d8e9f0a1b2c",
      "tgt_hash": "e3f4a5b6c7d8e9f0",
      "blocks_src": ["..."],
      "synced_at": "2026-10-21T09:40:00Z",
      "by": "human",
      "mode": "accept",
      "reviewed": true
    }
  }
}
```

**UI catalogs**: `.i18n/state/catalogs.fr.json`
```json
{
  "schema": 1,
  "keys": {
    "mcs:alarm.ack":            {"src": "a1b2c3d4e5f60718", "tgt": "0f1e2d3c4b5a6978", "reviewed": true},
    "mcs:pass.remaining_one":   {"src": "1122334455667788", "tgt": "8877665544332211", "reviewed": false},
    "db:tm.EPS_BAT_V.description": {"src": "aa00bb11cc22dd33", "tgt": "dd33cc22bb11aa00", "reviewed": false}
  }
}
```
Sidecars are committed to git. Hashes in the sidecar instead of the FR file's front matter keep the FR Markdown clean, the build untouched and diffs readable. The sidecar is the only file the tool owns.

### 7.3 Layout per component

**SMO suite**
```
smo_shared/static/shared/
  i18n.js                       # hand-rolled runtime (Section 1.2), served at /static/shared/i18n.js
  locales/en/{common,mcs,planner,instructor,rf,db}.json
  locales/fr/{...same...}.json
smo_shared/i18n.py              # t(key, lang, **args) over the same JSON; Babel formatting helpers
configs/...yaml                 # unchanged, EN only; source for db.json
docs/procedures/en/*.md   docs/procedures/fr/*.md
docs/manual/en/*.md       docs/manual/fr/*.md
.i18n/state/...  i18n.toml  i18n/glossary.csv
```
- A **language switcher** goes in the shared design-system header component. It is per browser; the wall display uses `?lang=`.
- **Migration order:** `common` → instructor console (smallest) → planner and wall → RF page → mcs.js (largest, about 4,900 lines; do it per panel). A quick grep inventory of `innerHTML`, `textContent =`, `title=` and `placeholder=` literals gives the work list.
- Server-to-UI messages move to `{code,args}` (Section 1.2).

**SpaceCDF**
```
frontend/src/locales/{en,fr}/*.json      # i18next JSON v4
frontend/src/i18n.ts                      # react-i18next init, Zustand-persisted lang
frontend/i18next.config.ts                # i18next-cli: extract/types/lint
frontend/eslint.config.js                 # + i18next.configs['flat/recommended']
backend/app/i18n.py                       # same t() helper reading frontend locales (or a copy)
backend agents: locale param → system prompt + glossary subset
.i18n/  i18n.toml  i18n/glossary.csv     # glossary shared with SMO (git submodule or copied)
```

**Teaching texts**
```
textbook/en/ch01-*.md ... textbook/fr/ch01-*.md
opsbook/en/...            opsbook/fr/...
oer/en/ch01..ch24.md      oer/fr/ch01..ch24.md
build/build_pdf.py --lang fr     # same scripts; sets <html lang="fr">, FR titles, FR running heads
.i18n/state/{textbook,opsbook,oer}/*.fr.json
```
- The build: pass `--lang`, pick the source tree, load FR strings for generated text ("Chapitre", "Table des matières", "Figure", "Tableau", "Équation") from a small `book.fr.json`, and set `lang="fr"` so WeasyPrint hyphenates in French (WeasyPrint uses Pyphen hyphenation dictionaries chosen by `lang`; prior knowledge). **Check that the body font has a U+202F glyph.** Some fonts lack it and fall back visibly.
- Math in French: in prose, `3,3 V`. Inside `$…$`, leave as authored (the protected-span rule). If French decimal commas are wanted in typeset math, the LaTeX convention is `3{,}3`. That is a separate, optional rule in the tool; do not let the LLM do it.

### 7.4 Workflow
1. Edit EN as usual. Commit.
2. pre-commit runs `i18n check`: errors block, stale content warns ("12 sections stale in opsbook/ch05").
3. When convenient, run `i18n translate --stale --emit .i18n/work/`, have Claude Code process the packets, then run `i18n apply`. Or use `--api` directly.
4. Review `git diff fr/` (optional), commit `i18n: sync FR`.
5. If someone fixes FR directly, `status` shows `FR_EDITED`. Review it, then `i18n accept`, and optionally `i18n backport-review`.

---

## 8. Effort estimate (rough)
- `i18n` tool (catalog plus YAML plus Markdown sections, check, status, emit/apply, typography): **3–5 focused days with Claude Code**, plus tests on one chapter of each book with real math, tables and attributes.
- SMO UI string extraction and runtime: **4–7 days** (mcs.js dominates). Server `{code,args}` refactor: 1–2 days.
- SpaceCDF react-i18next retrofit (144 files): **3–5 days**, mostly mechanical with i18next-cli and ESLint guiding it.
- Initial French of ~500k words: machine time plus spot review. Human review of the textbook is the real cost: budget it per chapter, starting with chapters students use first.

---

## 9. Not verified / caveats
- The po4a Text-module Markdown limitations (tables, math, re-wrapping) are from prior knowledge. The current man page would not render.
- Whether i18next's `dist/esm/i18next.js` imports cleanly in a browser without a bundler (it lists `@babel/runtime` as a dependency) was not tested. Vendoring the UMD build or using the hand-rolled runtime avoids the question.
- The French `Intl.PluralRules` `many` category, the exact CLDR spacing before `%`, and Babel's `Locale.negotiate` signature are from prior knowledge.
- ESA, CNES and EUMETSAT console number-format practice: no public source found.
- Whether a French-language edition of EN 16601-00-01 exists and is available, and whether CNES or ESA publish a downloadable EN-FR termbase: not verified.
- QuantEcon `action-translation`: its glossary JSON schema, whether its CLI works on non-MyST Markdown with kramdown attributes, and whether it can run same-repo (EN and FR folders in one repo) were not verified. **Trial it on one opsbook chapter before building the Markdown half from scratch.**
- Lingo.dev licence and whether its legacy local-LLM CLI is still maintained: not determined.
- IATE reuse conditions were not read in full.
- No API pricing figures are included. Check current Anthropic pricing and batch terms before the bulk first pass.

## 10. Sources
- i18next 26.0.0 release notes: https://newreleases.io/project/npm/i18next/release/26.0.0
- i18next package.json (25.8.16): https://cdn.jsdelivr.net/npm/i18next@25.8.16/package.json
- i18next-cli announcement: https://dev.to/adrai/supercharge-your-i18next-workflow-with-the-all-new-i18next-cli-341p
- @fluent/dom: https://www.npmjs.com/package/@fluent/dom
- MF2 / Intl.MessageFormat status: https://www.locize.com/blog/messageformat-2-i18next , https://github.com/tc39/proposal-intl-messageformat
- React i18n comparison (Jul 2026): https://tolgee.io/blog/react-i18n-libraries-comparison
- Lingui 6.0: https://js-lingui-2fbw45h8a-crowdin.vercel.app/blog/2026/04/22/announcing-lingui-6.0
- Paraglide JS README: https://unpkg.com/@inlang/paraglide-js@2.21.0/README.md
- eslint-plugin-i18next: https://www.npmjs.com/package/eslint-plugin-i18next
- CLDR French group separator change: https://www.unicode.org/mail-arch/unicode-ml/y2018-m09/0069.html
- Babel 2.18 / CLDR 47: https://mail-index.netbsd.org/pkgsrc-changes/2026/02/02/msg339599.html
- French typography (Debian FR): https://www.debian.org/international/french/typographie
- po4a Text module source: https://sources.debian.org/src/po4a/0.74-1/lib/Locale/Po4a/Text.pm
- mdpo: https://pypi.org/project/mdpo/
- Weblate Markdown format: https://docs.weblate.org/en/latest/formats/markdown.html
- Weblate machine translation (Anthropic backend): https://docs.weblate.org/fr/latest/admin/machine.html
- Lingo.dev lockfile / CLI: https://lingo.dev/en/cli/fundamentals/i18n-lock-lockfile
- GenAIScript continuous translations: https://microsoft.github.io/genaiscript/blog/continuous-translations
- QuantEcon action-translation: https://quantecon.github.io/action-translation , https://quantecon.github.io/action-translation/action-reference , https://quantecon.github.io/action-translation/cli-reference , https://quantecon.github.io/action-translation/heading-maps
- FranceTerme dataset: https://www.data.gouv.fr/datasets/base-franceterme-termes-scientifiques-et-techniques-1 ; sample space record: https://www.culture.fr/franceterme/france_terme_rtf?num=SPAT29 ; 2013 space vocabulary: https://www.culture.gouv.fr/content/download/93742/file/voca_en_ligne_2013_spatial_def.pdf
- IATE download: https://online-help.iate.europa.eu/technical-info/iate-download/
- EN 16601-00-01 (ECSS glossary): https://standards.iteh.ai/catalog/standards/cen/e83ab85e-b075-45e5-b16b-cea521fd0815/en-16601-00-01-2015
- Translation Bureau ISS glossary: https://publications.gc.ca/site/eng/9.582465/publication.html
- LLM terminology constraints (WMT 2025 example): https://arxiv.org/html/2510.17504v1
