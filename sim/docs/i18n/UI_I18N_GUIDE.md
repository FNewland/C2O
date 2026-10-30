# Modern UI translation guide (EN → FR), for packets S1–S4

Runtime: `/static/shared/i18n.js` (`smo-common/src/smo_common/ui/i18n.js`), no build, i18next‑v4 JSON. **The key is the
exact English text**, so English is the identity: in EN every page renders byte‑for‑byte what it does today, and the English
test suite is your regression net. Classic pages are out of scope (sha256 gate).

## 1. API

```js
import { I18n, t, tText, tHtml, tdb, getLang, onLangChange } from "/static/shared/i18n.js";  // never add ?v=
```

| Call | Use for | Escaping |
|---|---|---|
| `t(en, vars)` | anything inserted with `innerHTML` or a template literal | `{{x}}` values are HTML‑escaped; `{{- x}}` is raw |
| `tText(en, vars)` | `textContent`, `setText()`, `announce()`, `alert()`, `confirm()`, canvas `fillText`, `setAttribute` | none (the sink is not parsed as HTML) |
| `tHtml(en, vars)` | a template whose vars are **trusted markup** (`glyph()`, a rendered chip) | none |
| `tdb(key, en)` | YAML‑overlay text by stable id, e.g. `tdb("tm:eps.bat_voltage:description", p.description)` | none: keep the existing `esc()` |
| `vars.count` | plural: catalog keys `<en>_one`, `_many` (optional), `_other`. English other form = `vars.plural` | |
| `vars.context` | key `<en>_<context>` (falls back to `<en>`) | |

`getLang()` returns `"en"`/`"fr"`. `await I18n.ready` resolves at once in English, else after the catalogs (≤ 2.5 s).
`I18n.missing` (a `Set`; also `console.debug` once each): run `[...SMO_I18N.missing]` on a French page for your work list.
Interpolation never formats numbers: format first (§4).

## 2. Marking strings

**Static HTML.** Mark only **leaf text**. Never mark an element whose text the JS later rewrites; that text belongs in `t()`.

```html
<div class="q" data-i18n>Can I see it?</div>                 <!-- key = the text, whitespace-collapsed -->
<button data-i18n data-i18n-title title="Light/dark theme">THEME</button>
<input data-i18n-placeholder placeholder="Console note… (Enter logs it as your position)">
<span data-i18n-aria-label aria-label="server link"></span>
<b data-i18n data-i18n-context="power">BUS</b>               <!-- key BUS_power -->
```

* Empty `data-i18n` translates each direct text node and keeps child elements (`<span class="n">0</span> ALARMS` works);
  `data-i18n="key"` replaces `textContent`. `data-i18n-html` is for trusted catalog markup only.
* The English original is remembered, so EN is restored exactly. Keys are entity-decoded (`Keyboard & design`).
* `<title data-i18n>` works. SVG `<text data-i18n>` in `schematics.svg` also works, but only once the SVG is inlined: call
  `I18n.applyDom(svgRoot)` after mounting it.
* CSS‑generated text (`content:"STALE"` in `wide.html`) cannot be translated. Move it into a `<span data-i18n>`, or use
  `content: attr(data-label)` with `data-i18n-…`.

**JS.** Wrap the **whole sentence**, including its placeholders. Never wrap fragments: French word order differs.

```js
announce(tText("Blind-TC ARM — press again within {{s}} s to confirm…", { s: 8 }));
alert(tText("Could not read the start time — expected UTC YYYY-MM-DD HH:MM."));
ctx.fillText(tText("NOW"), x, y);                 // canvas: redraw on smo:langchange
el.title = tText("days of contact needed to drain");
```

## 3. Never translate (owner ruling R2)

Never pass any of the following through `t()`, and never include them inside a key. Put them in a `{{var}}` instead.

* telecommand mnemonics/names; parameter IDs (`eps.bat_voltage`) and hex ids (`0x02C5`); subsystem codes (EPS/TCS/AOCS/…)
* mode/state enums from config or TM (`SAFE`, `NOMINAL`, `COARSE_SUN (3)`, `ENABLED`); rate tiers (BEACON/LOW/HIGH)
* PUS labels (`S11`, `TC(3,5)`, `ENABLE (3,5)`, `S1.1`), SIDs, APIDs, procedure IDs (`LEOP-001`)
* units, CUC/ISO timestamps, `data_hex`, file names, API routes, keyboard keys, `EN`/`FR`, voice‑loop words (Go/No‑Go, R6)

Logic compares English values (`mode.label === "SAFE"`, `verdict.includes("FAIL")`). Compare the **untranslated** value and
translate only at display time. Server text (`reason`, `error_text`, event descriptions) stays English. Translate it by id with
`tdb()` once Y1 lands, or leave it.

## 4. Numbers

Engineering values keep the **decimal point** in every language (R5). Use `fmtNum(x, digits)` from `format.js` (always `.`,
never grouped) or the page's existing helper. Use `fmtProse(x, digits)` (French: `12 345,6`) **only** inside sentences an
operator will never type back. Never call `toLocaleString()` on telemetry.

## 5. Re-rendering on a language change

`setLang()` re-applies `data-i18n*` itself, then dispatches `smo:langchange`. Any region built in JS must be rebuilt from your
handler:

```js
onLangChange(() => { buildRail(); renderBottomDrawer(); drawTimeline(); });   // mcs.js: onLanguageChange()
```

* Each app already awaits `I18n.ready` before its first render (`mcs.js boot()`, `planner.js`/`instructor.js init()`) and
  mounts the toggle with `mountLangToggle($("lang-toggle"))`.
* Regions re-rendered every telemetry tick need nothing; add the rest (rails, tables built once, canvas, `<select>`, `title`).
* Wall display (`wide.js`): `I18n.init({ storage: false })` — no toggle, no localStorage; `?lang=fr` or server default.
* The instructor's `?ui=` propagation must also carry `?lang=` (S4).
* The rfsim `sim.html` page script is not a module. Use `window.SMO_I18N.tText(…)` from its `DOMContentLoaded` handler onwards.

## 6. Where the catalogs live

| Strings in | Catalog (`{}` until you fill it) | Served at |
|---|---|---|
| `components.js`, toggle, shared shell words | `smo-common/src/smo_common/ui/i18n/fr.json` (S0 owns) | `/static/shared/i18n/fr.json` |
| MCS `mcs.js`, `index.html`, `schematics.svg` | `smo-mcs/src/smo_mcs/static/modern/i18n/fr.json` | `/static/modern/i18n/fr.json` |
| planner `index.html`, `planner.js`, `wide.*` | `smo-planner/src/smo_planner/static/modern/i18n/fr.json` | same path on :9091 |
| instructor `index.html`, `instructor.js` | `smo-simulator/src/smo_simulator/instructor/static/modern/i18n/fr.json` | same path on :8080 |
| rfsim `index.html`, `sim.html` | `smo-rfsim/src/smo_rfsim/static/modern/i18n/fr.json` | same path on the rfsim port |
| YAML labels and descriptions (Y1, generated) | `smo_common/ui/i18n/fr.db.json`, a flat `{"kind:id:field": "texte"}` | `/static/shared/i18n/fr.db.json` |

App entries override shared ones. **S1 and S2 share the MCS catalog**: S1 adds keys for `mcs.js`, S2 for
`index.html`/`schematics.svg`. Keep each packet's keys in one contiguous block and merge, never overwrite. Use the shared
catalog for a word only when it means the same thing in every console.

## 7. Key conventions

* The key is the **exact English source literal**: same case, punctuation, `…`, `—` and spacing. `"ALARMS"` and `"Alarms"` are
  two keys.
* A placeholder name must be identical in the key and the value (`i18n check` and the S0 catalog test enforce this).
* Context suffix: use it only when one English word needs two French renderings, e.g. `"Mode_spacecraft"` vs `"Mode_planner"`
  (`t("Mode", { context: "spacecraft" })`).
* Plural: `"{{count}} pass_one": "{{count}} passage"` and `"{{count}} pass_other": "{{count}} passages"`. In French, 0 is `one`.
* `null` (what `i18n extract` writes) or `""` means untranslated: English is shown and the key is reported missing.
* French text follows `STYLE_FR.md` and `glossary.csv`. Keep labels within about 120 % of the English length.
* rfsim operator page: never put "POSTE", "impair…", "/sim" or any channel‑model word in `index.html`. It goes in the JSON
  catalog, not the HTML.

## 8. Worked example (mcs.js, command result line)

Before:

```js
setHTML("cmd-result", ok
  ? `sent TC(${service},${subtype})${name ? " — " + esc(name) : ""}`
  : `<span style="color:var(--alarm)">rejected — ${esc((r.json && (r.json.reason || r.json.error)) || `HTTP ${r.status}`)}</span>`);
```

After. The PUS label and the mnemonic `name` stay outside the sentence, and `t()` escapes `reason` exactly as `esc()` did:

```js
const reason = (r.json && (r.json.reason || r.json.error)) || `HTTP ${r.status}`;   // server text: English
setHTML("cmd-result", ok
  ? t("sent {{tc}}", { tc: `TC(${service},${subtype})` }) + (name ? " — " + esc(name) : "")
  : `<span style="color:var(--alarm)">${t("rejected — {{reason}}", { reason })}</span>`);
```

Add to `modern/i18n/fr.json`:

```json
{ "sent {{tc}}": "envoyé {{tc}}", "rejected — {{reason}}": "refusé — {{reason}}" }
```

English output is byte‑identical, so the node‑harness assertions keep passing.

## 9. Checks before handing back

1. UI test set no worse than baseline (survey §0); `tests/test_common/test_i18n_{runtime,server}.py` green.
2. Each page with `?lang=fr`: flip FR → EN → FR; EN pixel‑identical; `SMO_I18N.missing` empty.
3. Grep your diff: no mnemonic, hex id, mode enum or PUS label as a key.
