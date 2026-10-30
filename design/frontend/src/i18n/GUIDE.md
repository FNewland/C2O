# Translating SpaceCDF (EN → FR) — guide for packets C1–C4

Runtime: i18next + react-i18next, set up in `src/i18n/index.ts`. Your file list: `LIVE_FILES.md`.
French style and terms: `/home/claude/work/i18n/STYLE_FR.md` (form) and `glossary.csv` (terms; the glossary wins).
Target is international/European French, not Canadian.

## 1. The model: English text is the key
- `t('Run Analysis')` → `Run Analysis` in English, `Lancer l'analyse` in French.
- `locales/en.json` stays `{}`. A key missing everywhere renders as itself, so **English output must stay byte-identical**:
  wrap the exact existing literal, do not reword or re-punctuate it while wrapping.
- French goes in **your packet's own catalog** `locales/fr.c1.json` … `fr.c4.json` (flat JSON, keys sorted, UTF-8,
  real U+00A0/U+202F characters, 2-space indent). Never edit another packet's catalog or `fr.json` (C0's).
- An empty French value (`""`) means "not translated yet" and falls back to English.
- Keys are not split on `.` or `:` (keySeparator/nsSeparator are off), so full sentences are fine.

## 2. Usage
```tsx
import { useTranslation, Trans } from 'react-i18next'
import i18n, { fmtEng, fmtProse, fmtDate } from '../i18n'

function Panel({ n, name }: Props) {
  const { t } = useTranslation()            // re-renders when the language changes
  return <>
    <h3>{t('Mass Budget')}</h3>
    <input placeholder={t('Search components')} title={t('Filter by name')} />
    <p>{t('Element {{name}} has no parent', { name })}</p>
  </>
}
```
- Components: `const { t } = useTranslation()` at the top of each component that renders text.
- Outside React (event handlers in module scope, stores, `alert()`/`confirm()`): `i18n.t('…')`.
  Translate at the moment of display, never when building data that is stored.
- Module-level constants (`const LABELS = { 0: 'Mission' }`): keep the English value, call `t(LABELS[k])` when rendering.
  Add the comment `// English text is the i18n key` above such tables.
- Interpolation: `{{var}}` only. Never concatenate translated fragments (`t('Load failed: ') + msg` ✗ →
  `t('Load failed: {{message}}', { message })` ✓). Values are not HTML-escaped by i18next; React escapes them.
- `title=`, `placeholder=`, `aria-label=`, `alt=`, `confirm()`, `alert()` and SVG `<text>` are translated like visible text.

## 3. Embedded markup: `<Trans>`
```tsx
<Trans i18nKey="Click <1>Run Analysis</1> to fill the budgets." components={{ 1: <strong /> }} />
```
French: `"Click <1>Run Analysis</1> to fill the budgets.": "Cliquez sur <1>Lancer l'analyse</1> pour compléter les bilans."`
Keep the same numbered tags; move them as French word order requires. Use `<Trans>` only when markup sits inside a sentence;
otherwise translate each text node with `t()`.

## 4. Plurals and context
- Key = English plural form; English singular via `defaultValue_one`:
  `t('{{count}} elements', { count: n, defaultValue_one: '{{count}} element' })`
- French entries: `"{{count}} elements_one"`, `"{{count}} elements_other"`, and `"{{count}} elements_many"` (used for
  1 000 000+ in French: "1000000 d'éléments"). French `_one` covers 0 and 1.
- Context when one English word has two French renderings: `t('Open', { context: 'state' })` → fr key `Open_state`
  ("Ouvert") vs `t('Open')` ("Ouvrir"). English falls back to the bare key automatically.
- No gender/number agreement by string assembly: write whole sentences.

## 5. Never translate (leave literal, do not wrap in `t()`)
- Standard numbers and titles: `ECSS-E-ST-10C`, `ECSS-Q-ST-30C`, `NASA SP-2016-6105`, `CCSDS 133.0-B`, `ISO 15288`, `CDS`.
- Identifiers: element/requirement/interface/function IDs and codes (`MIS-001`, `SYS-PWR-003`, `IF-12`), parameter IDs
  (`eps.power_w`), enum values (`draft`, `subsystem`, `space`, `bidirectional`), API paths, JSON keys, CSS, `localStorage` keys.
- Units and symbols (`kg`, `W`, `Wh`, `dB`, `dBW`, `km`, `kbit/s`, `°C`, `%`), mnemonics and acronyms used as names
  (`EPS`, `AOCS`, `OBC`, `TT&C`, `ADCS`, `SRR/PDR/CDR`, `TRL`, `FMECA`, `ICD`, `V&V`), part numbers and products
  (`GomSpace NanoPower P31u`, `Ti-6Al-4V`). A label containing one is translated around it: `Masse EPS (kg)`.
- **Values stored to the backend.** Seed names in `designStore.ts`, `BlocksPanel.tsx`, `MissionWizard.tsx` and
  `suggestedReqs.ts` (and `'New Mission'`, `'Loaded Mission'` in `App.tsx`) become element names, requirement text or
  study names in the database. Do not change the literal that is sent; translate only where it is *displayed*, and only
  while it still equals the seed (a user-edited name is user data and is never translated).
- Backend text shown verbatim (`detail` of HTTP errors, closure/analysis messages, export file names): stays English this wave.
- Voice-loop words if any appear (Go/No-Go, Hold, Mark): English (owner ruling R6).

## 6. Numbers and dates
- Engineering values keep the decimal **point** in French (ruling R5): use `fmtEng(v, d)` (same as `v.toFixed(d)`) or leave
  existing `toFixed` calls alone. This covers tables of results, budgets, inputs the user types back, chart tick labels.
- Numbers inside translated prose may use `fmtProse(v, opts)` (fr-FR: `12 345,6`; en: `12,345.6`).
- `toLocaleString()` / `toLocaleDateString()` with no locale → `fmtProse()` / `fmtDate()` so they follow the UI language,
  not the browser's.
- In French catalog text: U+00A0 before `:` and between a number and its unit (`5 W`); U+202F before `; ! ?` and inside
  « guillemets »; `…` (U+2026) for `...`; sentence case for Title Case labels; buttons in the infinitive.

## 7. Length and layout
Aim for ≤ 120 % of the English length; abbreviate with a full stop (`Puiss.`, `Tps`) rather than overflow fixed-width
buttons and table headers. Check the panel at 1280 px wide in both languages.

## 8. Checklist before you hand back
1. English UI unchanged (switch to EN, compare with `git stash` build or screenshots).
2. `npx tsc -b 2>&1 | grep -c "error TS"` is **not higher** than the C0 baseline (105, all pre-existing).
3. `npx vite build` succeeds.
4. Every `t()` key you added has a French entry in your catalog with the same `{{placeholders}}` and `<n>` tags.
5. No identifier, unit, standard number or stored value was translated (§5).
6. Only files listed for your packet in `LIVE_FILES.md` were touched (plus your `fr.cN.json`).

## Backend (for reference)
- AI design agents answer in the UI language: send `language: getLang()` in the `/api/ai/ask` body (`aiLanguageField()`
  helper) or `?language=fr` on `/api/ai/critique-need|write-requirements|review-design`. Default is English.
- `POST /api/exports/docs/{study_id}?lang=fr` picks `exporters/docs/templates/fr/<review>.md.j2` when it exists.
  TODO (C2 / K3): those French templates do not exist yet; Word/Excel generators and the other export routes are English-only.
