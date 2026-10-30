# UI String Survey — English/French i18n planning (SMO modern UIs + SpaceCDF)

Date: 2026-10-28. Read-only survey; no code was modified.
Repos: `/home/claude/work/smo` (baseline commit `983af0f`), `/home/claude/work/cdf` (baseline `be16bc3`).

Counting method: an AST walk (TypeScript compiler API, `/opt/npm-tools/node_modules/typescript`) over every JS/TS/TSX file collects
string literals, template literals, JSX text and HTML fragments inside literals, excluding import paths, property keys, `===`
comparands, `case` labels, and first arguments of DOM/fetch/classList-type calls. HTML/SVG files use an HTML parser (text nodes plus
`title`/`placeholder`/`aria-label`/`alt`/`label` attributes). The "raw" figures still include engineering mnemonics (EPS, RW3, S15,
0x0700), CSS fragments and URL tails. Hand sampling puts the share of genuine translatable prose at about 70–75%. Both figures are
given below.

---

## 0. Headline findings

1. **No i18n infrastructure exists in either codebase.** SMO has no `lang` handling at all, and every modern page is `<html lang="en">`.
   CDF has a single unused knob, `OutputConfig.language = "en"`
   (`cdf/packages/spacecdf-ai/src/spacecdf_ai/config.py:26`; `configs/genai.yaml:50` "future: multi-language"). Nothing reads it.
2. **`why-this-design.html` does not exist.** It was deleted deliberately: `tests/test_e2e_browser/inventory_checklist.md:209` says
   "DELETED 2026-08-19 (owner ruling: no training mode)". `tests/test_mcs/test_modern_page_behaviour.py:731-741`
   (`test_training_layer_fully_retired`) asserts that it, `guided-btn`, `data-ann` and `/api/annotations` are absent. The baseline
   `modern/index.html` still contains `guided-btn` (line 267), `data-ann` (lines 320, 343, 375) and the link (line 405), so that test
   **fails at baseline**. `configs/eosat1/mcs/annotations.yaml` also no longer exists. `/api/annotations` always returns `{}`
   (`server.py:4591`) and its two tables moved to `mcs/display_config.yaml` (`/api/display-config`). Guided-mode text is therefore
   **not** a translation source.
3. **The SMO baseline is not green.** Running the UI-related tests here gives `12 failed, 209 passed, 5 errors`. Separately, 4
   modules fail to collect because `aiohttp`, `sgp4` and `tools/vr_stub/vr_stub.py` are missing in this container. The failures are
   9 in `test_modern_page_behaviour.py`, plus `test_modern_inventory.py::test_route_snapshot_is_current` (`/api/procedure/cards` is
   not in the snapshot), `test_every_modern_js_api_path_has_a_route[mcs]` and
   `test_pus_command_payload_contract.py::test_every_modern_pus_payload_uses_data_hex`. Translation agents must diff against this
   baseline and must not expect a green run.
4. **92 of 144 CDF frontend files cannot be reached from `main.tsx`.** These are dead components such as `components/UserManual.tsx`
   (230 strings), `EquipmentBrowser.tsx`, `ProjectManagement.tsx`, all of `phases/*`, `views/LensView.tsx` and `constants.ts`.
   `App.tsx:10-21` imports only the workbench. Only 52 files (~14.8k lines) are live. Translating the dead files would roughly
   double the CDF work for no visible gain.
5. **The bulk of the SMO text is server/config content, not UI chrome.** The UI chrome totals about 1,300 strings. The YAML catalogs
   hold about 2,600 prose strings (~17k words), and the procedures and manual Markdown hold about 162k words. The two need separate
   tracks with different mechanisms.

---

## 1. How user-visible text is produced (SMO modern UIs)

### 1.1 Per-file mechanism and counts

| File | Lines | Mechanism | Raw distinct | Est. translatable |
|---|---|---|---|---|
| `smo-mcs/.../static/modern/index.html` | 416 | static HTML shell (header, SA cards, drawer tabs, alarm drawer, dialogs), `title`/`aria-label`/`placeholder` | 104 (81 text, 13 aria, 7 title, 3 placeholder) | ~85 |
| `smo-mcs/.../static/modern/mcs.js` | 4,891 | "All rendering is string-composition + innerHTML" (header comment, line 5): template literals into `setHTML()`/`innerHTML` (42 sites), `setText()`/`textContent` (16), `announce()` aria-live messages, one canvas `fillText` (l.1014 "NOW"), Chart.js trend labels, object-literal tables (`POSITION_INFO` l.159, subsystem titles l.760/1106, stepper `states:` arrays l.1094-1115) | 822 (373 HTML text, 299 plain literals, 114 templates, 27 placeholders, 6 aria, 3 title) | ~575 (rest are mnemonics) |
| `smo-mcs/.../static/modern/schematics.svg` | 253 | 123 `<text>` labels, 112 distinct | 112 | ~25 (most are mnemonics: `RW1`, `PL3 PAYLOAD`, `BAT · 0x0407`) |
| `smo-planner/.../static/modern/index.html` | 431 | static HTML | 97 (85 text, 10 title) | ~85 |
| `smo-planner/.../static/modern/planner.js` | 1,352 | **string concatenation** (one backtick in the file), `innerHTML` (24), `textContent` (33), 18 `alert()`, 4 `confirm()`, 5 canvas `fillText`, `.title=` (8) | 203 | ~150 |
| `smo-planner/.../static/modern/wide.html` | 360 | static HTML; **CSS-generated text** `content:"STALE"` (l.142) | 22 | ~20 |
| `smo-planner/.../static/modern/wide.js` | 1,214 | `textContent` (45), canvas `fillText` (8), small `innerHTML` (3) | 70 | ~50 |
| `smo-planner/.../static/modern/wide-basemap.js` | 176 | coastline data only | 0 | 0 |
| `smo-simulator/.../instructor/static/modern/index.html` | 589 | static HTML (header, speed group, interventions column) | 128 (110 text, 13 title) | ~110 |
| `smo-simulator/.../instructor/static/modern/instructor.js` | 1,257 | template literals into `innerHTML` (31), `textContent` (31), `createElement` (7), log lines | 161 | ~110 |
| `smo-rfsim/.../static/modern/index.html` | 618 | static HTML plus an **inline `<script type="module">`** (l.209, ~407 lines): `textContent`, canvas `fillText` axis labels (l.267, 511, 522-523), `canvasNote()` | 58 HTML + 40 script | ~80 |
| `smo-rfsim/.../static/modern/sim.html` | 282 | static HTML plus an **inline classic `<script>`** (l.148, ~132 lines) | 56 HTML + 12 script | ~55 |
| `smo-common/.../ui/components.js` | 675 | shared renderers that return HTML strings (`renderParam`, `renderAndTable` headers l.325-326, `renderAlarmRow` "ACK"/"PROCEDURE", severity "CRIT/HIGH/MED/INFO" l.465, "NOT ENABLED" l.295/534, "no limit defined" l.139/167, "INSTRUCTOR" badge l.467) | 40 | ~25 |
| `smo-common/.../ui/format.js` | 186 | unit suffixes only (`"MET "`, `" s"`, `" m "`, `" h "`, `"> 1 d"`) | ~6 | ~6 |
| `smo-common/.../ui/glyphs.svg` | 80 | symbol ids | 9 | 0 |
| **SMO UI total** | | | **~1,960 raw** | **~1,300** |

Not present: `alert()`/`confirm()` in mcs.js or instructor.js; `toLocale*` anywhere except planner.js:625/632 and rfsim
`toLocaleTimeString` (index.html:456, sim.html:196).

### 1.2 Representative examples (file:line)

- MCS shell: `index.html:251` "Skip to main content"; `:277` SA card "Can I see it?" (plus "Can I talk?", "Is it well?",
  "What's next?"); `:329` placeholder "Console note… (Enter logs it as your position)"; `:377` "Blink is reserved for
  unacknowledged P1…"; `:392` "Keyboard &amp; design".
- mcs.js: `:159-167` `POSITION_INFO` titles ("POWER & THERMAL", "FLIGHT DYNAMICS / AOCS"); `:760` "Attitude & orbit control";
  `:1094-1115` stepper labels "Load shed ladder", "FPA cooldown", "AOCS mode chain"; `:1817/1830` reason strings "planner_url not
  configured — confirm the burn plan by voice with FDS"; `:1873` "Do NOT arm until FDS confirms which is right (PR4)"; `:1889`
  `announce("Blind-TC ARM — press again within 8 s to confirm…")`; `:1014` canvas `fillText("NOW")`; `:2556` "rejected — ${reason}".
- planner.js: `:602` `confirm("Delete activity #" + id + "?")`; `:669` `alert("Could not read the start time — expected UTC
  YYYY-MM-DD HH:MM.")`; `:528` canvas "NOW (wall clock)"; `:1091` "days of contact needed to drain".
- wide.js: `:557` canvas "NEXT ORBIT"; `:562` "… MIN — DERIVED FROM …"; `:589-590` "CONTACTS"/"ACTIVITIES"; wide.html `:243`
  "DISPLAY STALE — NO DATA FOR".
- instructor: `index.html:285` "Instructor console — simulation ground truth · not an operator display"; `:418` "TRUE OFFSET";
  `:567` "OVERRIDE PASSES"; instructor.js `:449` "Stop refused: …", `:950` "VR bridge not running (--no-vr, SMO_VR=0 or port in
  use)", `:1170` "← Back to dashboard".
- rfsim: `index.html:88` "Bit sync"; `:180` "Eye diagram"; `:440` canvasNote "Eye diagram: RF mode only"; `sim.html:70` "Channel
  model status".

### 1.3 Text that must stay English (engineering identifiers)

The following are mission vocabulary that procedures, packet dumps and S12 definitions quote verbatim. They should not be
translated:

- PUS service/subtype labels ("ENABLE (3,5)", "DUMP (15,9)", "S11 sent")
- parameter mnemonics and hex ids (`aocs.fine_ready 0x02C5`)
- subsystem codes (EPS/TCS/AOCS/TTC/PLD/PRP/OBD)
- rail codes (`RAIL`, mcs.js:150)
- mode names served from config (`SAFE`, `NOMINAL`, `DETUMBLE`)
- schematic mnemonics

mcs.js:726 compares `mode.label === "SAFE" || "EMERGENCY"`, and mcs.js:2586 does `v.verdict.includes("FAIL")`. If those values are
ever localized, the logic breaks.

---

## 2. Server-originated text (SMO)

### 2.1 MCS endpoints that deliver displayed prose

All routes are registered in `smo-mcs/src/smo_mcs/server.py:1383-1481`. mcs.js reads `.label` ×29, `.description` ×15, `.units` ×8,
`.reason` ×8, `.message` ×6, `.detail` ×5, `.situation` ×2, `.error_text` ×2 and `.fd_decision` ×1.

| Endpoint | Displayed fields | Origin |
|---|---|---|
| `/api/param-catalog` (`_handle_param_catalog` l.3277) | `description`, `units`, `states{code:name}` | `configs/eosat1/telemetry/parameters.yaml` (407 descriptions, 3.0k words). State names are parsed from description prose by `smo_common/telemetry/eng_values.py` (`build_state_tables`). **State names are mnemonics; keep them.** |
| `/api/tc-catalog` (l.3352) | command `description`, field `label`, `group`, quick-command names | `commands/tc_catalog.yaml` (522 descriptions, 127 labels, 64 groups; 5.6k words) |
| `/api/failure-codes` (l.3221) | code → meaning | `smo_common/protocol/pus_services.py:33` `FAILURE_CODES` (50 entries) and `:120` `MEMORY_FAILURE_CODES` (4) |
| `/api/verification-log`, WS events | `error_text`, `reason` | `error_text` comes from `failure_code_text()` (server.py:1768/1809). `reason` is **free text downlinked in the S5 aux field by the simulator** and parsed back by the regex `_REJECTION_AUX_RE` (`pus_services.py:195`, format built at l.205-211: "`{identity} rejected at {stage}, err 0x…: {reason}`"). Translating it server-side would break the parser. |
| S5 events / alarms (`/api/alarms`, WS `events`) | event `description`, alarm `value` | Event text is the **on-board aux string** decoded at `tm_processor.py:89`. Alarm `value` = event description (server.py:1938). Limit alarms are built at server.py:1976-1990 (`limit` = `"RED_HIGH > 42"`). Translation is only possible client-side by `event_id` against `events/event_catalog.yaml` (153 descriptions, 1.1k words), which is also loaded at server.py:798 as `_event_meta`. |
| `/api/fdir` (l.4408) | S12/S19 rule names and descriptions, journal | `monitoring/s12_definitions.yaml` (41 names + 41 descriptions), `monitoring/s19_rules.yaml` (32), `fdir/fault_propagation.yaml` (42), plus `fdir/procedures/*.yaml` (10 files) |
| `/api/procedure/cards` (l.4022), `/api/procedures`, `/api/procedures/{path}`, `/api/procedure/status` | step `description`, procedure names, position roles, runner messages | `procedures/procedure_index.yaml` (67 names, ~145 per-position role strings; 887 words); `procedures/**/*.md` (67 files, **92,120 words**); `procedure_runner.py` (43 prose literals) |
| `/api/manual`, `/api/manual/{path}` | rendered Markdown (client `renderMarkdown`, mcs.js:3567) | `configs/eosat1/manual/*.md` (20 files, **70,071 words**) |
| `/api/positions` (l.3204) | `label`, `display_name` | `mcs/positions.yaml` (10 strings) — mcs.js also hard-codes `POSITION_INFO` |
| `/api/gonogo-matrix` (l.4652) | `situation`, `fd_decision`, `reason` | `mcs/gonogo_matrix.yaml` (22 strings) |
| `/api/display-config` | gate `label`s | `mcs/display_config.yaml` (11 labels) |
| `/api/displays/*`, `mcs/displays.yaml` | panel labels | `mcs/displays.yaml` (152 labels + 36 names); `displays/system_overview.py` (11 literals) |
| `/api/hk-structures` | SID names | `telemetry/hk_structures.yaml`; `sid_names` also in `/api/client-config` |
| `/api/displays/link-prediction` | `reason` | `link_prediction.py` (6 literals) |
| `/api/console-log` | server auto-entries `text` | `server.py:_console_log()` (l.4686) callers |
| `POST /api/pus-command` | `message` | server.py:2956 "Service N not allowed for position P" (from `_check_position_access` l.986/995), :2991 "No TC connection", :3003 `str(e)` |
| derived params | labels/units | `derived_params.py` (24 literals), `telemetry/derived.yaml` (11) |
| `mcs/pus_services.yaml` | panel labels/descriptions | 32 strings |

In total, smo-mcs Python holds about 168 prose literals (52 in server.py, 43 in procedure_runner.py, 24 in derived_params.py, 23 in
tm_archive.py).

### 2.2 Planner

- `/api/constraints/*`, `/api/schedule/validate` return violation `message` and `suggested_fix`, built as f-strings in
  `constraint_checkers.py` (l.98, 188, 311, 360, 462, 519…).
- Further prose comes from `budget_tracker.py` (30), `planner_config.py` (31), `activity_scheduler.py` (16), `server.py` (22) and
  `plan_templates.py` (18).
- `/api/activity-types` and `/api/schedule/templates` serve names from `configs/eosat1/planning/{activity_types,standard_plans,
  imaging_targets,ground_stations}.yaml`.
- planner.js shows server `error` text verbatim inside `alert()` (l.694, 762, 838, 1266).

### 2.3 Instructor (simulator)

- `/api/failure-catalog` → `smo_simulator/failure_catalog.py:to_dict()` aggregates `FailureSpec(label=, effect=, …)` and
  `ParamSpec(label=, description=)` from `models/*_basic.py`: 54 specs (aocs 11, eps 9, obdh 10, payload 5, prop 4, tcs 7, ttc 8),
  about 137 text fields plus parameter labels.
- `/api/scenarios` and `/api/scenario/debrief` serve `configs/eosat1/scenarios/*.yaml` (38 files, 261 prose strings, 4,680 words:
  166 descriptions, 38 briefings, 37 names).
- Injection rejections arrive as "REJECTED: {reason}" (instructor.js:706).

### 2.4 RF sim

- `/api/status` and `/api/config` (`smo_rfsim/radio/web_ui.py:200-205`) serve mostly numeric data and state words.
- `web_ui.py` holds 5 message literals.

### 2.5 Recommendation for server content

Keep all API strings English. That protects the S5 regex contract, the server-side tests listed in §5.3 and the realism of
spacecraft-generated text. Localize by **id-keyed overlays** fetched by the client, along these lines:

- `configs/eosat1/i18n/fr/{parameters,tc_catalog,events,s12,s19,fdir,procedure_index,positions,gonogo,displays,display_config,
  failure_codes}.yaml`, keyed by hex id, command name, event id or rule id.
- Serve them either as static JSON or as an additive `?lang=fr` on the existing endpoints. Prefer static, because new routes trip
  the route snapshots (§4).

Markdown procedures and the manual (162k words) are a separate document-translation project and should be scheduled separately.

---

## 3. Number, date and time formatting

- **`smo-common/src/smo_common/ui/format.js`** (frozen "additive only" contract, header l.8-10) is the only shared formatter set:
  `fmtUTC` (l.43), `fmtMET` (l.67, `"MET DDD/HH:MM:SS"`), `fmtCUC` (l.97), `fmtAge` (l.125: `"0.4 s"`, `"3 m 05 s"`, `"> 1 d"`),
  `fmtHex` (l.151). All are UTC-only and never apply a local zone. **There is no numeric formatter in format.js.**
- Numeric formatting is scattered:
  - `components.js:_num()` (l.660-666) handles exponent, integer and 2/1/0 dp; `components.js:_age()` is l.668.
  - mcs.js: `num(v, dp)` (l.175), a decimals helper (l.2089), `engValue()` (l.271, which appends `NAME (code)`) and
    `fmtDerivedValue()` (l.1412, `MB`/`kB`).
  - planner.js has 41 bare `toFixed`, wide.js 17, instructor.js 7, rfsim index.html ~25 (l.384-436, 511-523) and sim.html ~6.
  - planner.js:625-632 is the one use of `Intl.DateTimeFormat`/`toLocaleString`. It deliberately shows the operator's local time
    next to UTC.
  - rfsim `toLocaleTimeString()` (index.html:456, sim.html:196) already follows the browser locale.
- **How locale would plug in:**
  - Add `fmtNum(v, dp, {locale})` and `fmtUnit()` to format.js. That change is additive, so it is allowed.
  - Route `num()`, `_num()` and the bare `toFixed` sites through them.
  - Translate the unit-word suffixes in `fmtAge`/`fmtMET` (`d` → `j`, keep `s/m/h`; "MET" → keep or "TEM").
- **Open decision for the owner:** should French engineering values use a decimal comma? Ops convention (and pasted values,
  `data hex`, S11 time tags, S12 thresholds that operators type back) argues for **keeping `.` in numeric values on the consoles**
  and localizing prose only. If the comma is chosen, every input parser (planner SoC input, S11 time fields, instructor magnitude
  inputs) must stay dot-tolerant. ISO timestamps, CUC hex and parameter ids must never be localized.

---

## 4. How the modern UIs are served, and where the language hook goes

| Server | Modern route(s) | UI switch |
|---|---|---|
| MCS (aiohttp) | `/`, `/modern` (server.py:1383-1388); `_resolve_ui` l.3096; `_index_file_for` → `static/modern/index.html` l.3104 | CLI `--ui` (l.5474) > `SMO_UI` env > mission.yaml `ui:` (`smo_common/config/schemas.py:60-69`) > default `"modern"` (l.191-196). Per-request `?ui=` wins (l.3098). |
| Planner | `/`, `/modern`, `/wide` (l.469-470; wide → `modern/wide.html` l.954-959) | same chain (server.py:143-150, `--ui` l.1760, `?ui=` l.905) |
| Instructor | `/`, `/modern` (`instructor/app.py:60-63`) | explicit arg from simulator `--ui` (`smo_simulator/server.py:218`) > `SMO_UI` > `"modern"` (app.py:53). instructor.js propagates `?ui=` into sub-page and back links (l.271-275, l.1160-1168). |
| RF sim | `/`, `/modern`, `/sim` (`radio/web_ui.py:136-139`) | `--ui` (bridge.py:933) > `SMO_UI` > `"modern"` (web_ui.py:86-88) |

- All three Python servers mount `/static/shared/` from `smo_common/ui` before `/static/` (MCS server.py:1537-1541, planner
  l.546-551, rfsim web_ui.py:146-151, instructor app.py:141). Own assets carry `Cache-Control: no-cache` (MCS l.1375-1381).
- **Existing per-viewer preference precedent:** MCS `localStorage` keys `mcs.theme`, `mcs.position` and `mcs.alarmFilters`
  (mcs.js:532, 4163, 4370, 4818-4820), plus the THEME/GREY header buttons (index.html:269-272).

**Recommended hook**

1. **Client:** add a shared `/static/shared/i18n.js` exporting `t()` and `getLang()`. Resolution order: `?lang=` >
   `localStorage["smo.lang"]` > server default > `"en"`. It sets `document.documentElement.lang` and applies `data-i18n`
   attributes to static HTML. Add a header EN/FR toggle next to THEME (MCS), the header (planner and instructor), and the rfsim
   pages.
2. **Server default (additive JSON fields only, no new routes):**
   - MCS: add `"lang"` to `/api/client-config` (`_handle_client_config`, server.py:4872).
   - Planner: `/api/config/planner` (l.482).
   - Instructor: `/api/state`.
   - rfsim: `/api/config`.
   - Source: the same precedence chain as `ui`, i.e. `--lang` > `SMO_LANG` > a mission.yaml `lang:` field added beside `ui:` in
     `schemas.py`.
3. **Dictionaries as static files.** Use `/static/shared/i18n/fr.json` (shared components) and `static/modern/i18n/<page>.fr.json`
   per app. They are served by the existing static mounts, so **zero new routes**. That matters because the MCS, planner and
   instructor route snapshots fail on any unlisted route (`test_route_snapshot_is_current`), and the rfsim snapshot is an exact
   **set equality** (`tests/test_rfsim/test_radio_ui_split.py:188-211`).
4. **Keys:** use the English source string as the key (gettext style, `t("CANNOT BE COMPUTED")`). The English literal then stays in
   the source and en output is byte-identical, which keeps the many grep-style tests (§5) green. Opaque keys would break them.
5. Propagate `lang` the way instructor.js already propagates `ui` (l.271-275, 1160-1168), and on cross-app links (MCS → `/dumps`,
   `/reports`; planner → `/config`).

---

## 5. Tests that would break if HTML/JS text changed

### 5.1 Byte-freeze gates (classic pages; out of scope, must not be touched)

- `tests/test_common/test_classic_untouched.py:24-46`: sha256 of the four classic pages.
- The same check is re-asserted in `tests/test_content/test_modern_inventory.py:250-256`,
  `tests/test_mcs/test_modern_page_behaviour.py:695`, `tests/test_planner/test_modern_page.py:157` and
  `tests/test_simulator/test_instructor_modern.py:28,267`.

### 5.2 Route snapshots (break only if routes are added or removed)

- `tests/test_content/test_modern_inventory.py`:
  - `test_no_pre_existing_route_disappears` (MCS, planner, instructor, dump_store, reporting, confedit)
  - `test_route_snapshot_is_current` (new routes must be appended; **failing at baseline** for `/api/procedure/cards`)
  - `test_every_modern_js_api_path_has_a_route` (every `/api/...` literal in modern JS must exist)
- `tests/test_rfsim/test_radio_ui_split.py:188-211`: exact set equality.

### 5.3 String and source-shape assertions

Approximate counts of string-asserting lines per file:

- `tests/test_mcs/test_modern_page_behaviour.py`: ~117. Uses the node harness `tests/test_mcs/js/modern_harness.js` to run mcs.js
  and asserts English output such as "tier LOW", "NO TM", "TRAINING · SIM x5", "no limit defined" and "line overcurrent".
  **The harness copies only `components.js` and `format.js` and rewrites only those two import specifiers (l.33-37), so a new
  `import … from "/static/shared/i18n.js"` in mcs.js breaks every harness-based test until the harness is updated.** Other
  harness users: `test_staleness_parity.py` ("NOMINAL (4)", "OFF (0)", "COARSE_SUN (3)", "NOT ENABLED"),
  `test_hk_enable_reset_visibility.py`, `test_quick_command_bytes.py`, `test_pus_command_payload_contract.py`,
  `test_lazy_panel_click_binding.py` (regexes on code shape, e.g. `function panelResult(id, msg, bad)` l.98).
- `tests/test_mcs/test_modern_page_behaviour.py:731-741`: absence of the training layer. A `date` rule also restricts `Date.now()`
  to section 1 (mcs.js header l.28-30).
- `tests/test_planner/test_modern_page.py` (~23): "CANNOT BE COMPUTED" (l.192), "WILL NOT FIT" (l.202), "DUMP FIT"/"ACHIEVABLE"
  (l.204), "No rfsim URL configured" (l.219), `for="socInput"` label.
- `tests/test_planner/test_wide_page.py` (~32): `"AOS "`/`"LOS "` in the track function (l.365), font-size floors, `id="staleBanner"`,
  `PAGE_STALE_MS`.
- `tests/test_simulator/test_instructor_modern.py` (~23): `[Ii]nstructor console` (l.178), "TRUE OFFSET" (l.200), "not downlinked"
  (l.201), `markup.count("OVERRIDE PASSES") == 1` (l.208), "Back to dashboard" (l.258), "PDF instructions" absent (l.223).
- `tests/test_rfsim/test_radio_ui_split.py`:
  - `CHANNEL_MODEL_TOKENS` must be **absent** from the operator page (l.39-46). **French pitfalls:** "impair" is a French word
    (odd), so it must not appear in the operator HTML.
  - `"POST" not in html.upper()` (l.69). **French "POSTE" ("position") would fail it.**
  - `/sim` must be absent.
  - The legit English words "carrier", "bit sync", "eye diagram", "doppler", "link budget", … must be **present** (l.75-78).
  - Recommendation: keep French dictionaries out of `modern/index.html` (put them in a JSON file) and keep the English source text
    in the HTML.
- `tests/test_instructor_render_completeness.py` (6) and `tests/test_common/test_ui_switch.py` ("not installed" l.244).
- **E2E (Playwright)**: `tests/test_e2e_browser/test_modern_ui.py` (skipped unless `SMO_E2E=1`, l.36) asserts "Wall Display"
  (l.176/182) and non-empty `#sa-well-v`. `inventory_checklist.md` cites `index.html` line numbers, which drift when HTML changes.
- **Server-string tests (only matter if server text is localized):** `test_mcs/test_verification_failure_display.py`,
  `test_mcs/test_error_code_visibility.py` (23), `test_mcs/test_procedure_convergence.py`, `test_planner/test_fly_a_plan.py`,
  `test_integration/test_planner_mcs_s11_chain.py`, `test_simulator/test_payload_2026_08b.py`,
  `test_simulator/test_simulation_config.py`.

**Rule of thumb:** with gettext-style English keys and English as the default language, none of these assertions change. The only
mandatory test-infra edit is to `modern_harness.js`. Optionally add a new gate that every `t("…")` key has an `fr.json` entry.

---

## 6. SpaceCDF

### 6.1 Frontend structure

- React 19, Vite 8, TS 6, zustand, react-query, `@xyflow/react` (`frontend/package.json`).
- Entry: `index.html` → `src/main.tsx` → `App.tsx`. 144 files and 35.6k lines, of which **52 files (~14.8k lines) are live**. `App.tsx`
  imports `LevelWorkbench`, `MissionWizard`, `ReadinessChecklist`, `EscalationBanner`, `ExportPanel`, `GuidancePanel`, `PresenceBar`,
  `MarginTower` and `ai/*` (l.10-21).
- Served by the Vite dev server (README l.59-64; `vite.config.ts` proxies `/api` and `/ws` to :8000). FastAPI does not mount the
  build: `StaticFiles` is imported but unused (`app.py:13`). `node_modules` is not installed in this copy, so `tsc -b` cannot run
  here.
- No i18n library, no string tables. `constants.ts` (`POSITION_OPTIONS` labels) is itself unreachable. `uiStore.ts` is the natural
  home for `lang`, and `localStorage` is already used (`spacecdf-pugh`, `spacecdf-risks-*`, `spacecdf-options`).
- **Mechanisms:** JSX text, string literals in data arrays (guidance steps, trade criteria, seed templates), `title=`/`placeholder=`
  (95 in live files), `confirm()`/`alert()` (20, e.g. `BlocksPanel.tsx:340`), SVG `<text>` charts (20, e.g.
  `charts/SVGLineChart.tsx:152,166`), `toFixed` (102 in live files), `toLocaleString`/`toLocaleDateString` (`DecisionPanel.tsx:667-668`,
  `MissionWizard.tsx:698`).

**Live-file string counts** (raw; translatable is about 70%):

| Files | Raw strings |
|---|---|
| `workbench/DecisionPanel.tsx` | 204 |
| `workbench/BlocksPanel.tsx` | 191 (largely seed and catalog data: "CubeSat LEO Mission", "Ti-6Al-4V") |
| `workbench/GuidancePanel.tsx` | 147 |
| `workbench/ExportPanel.tsx` | 142 |
| `workbench/VVPanel.tsx` | 134 |
| `workbench/MissionWizard.tsx` | 110 |
| `components/PhysicsClosurePanel.tsx` | 89 |
| `components/VVPlanPanel.tsx` | 65 |
| `components/GroundSegmentPanel.tsx` | 65 |
| `workbench/DesignTools.tsx` | 58 |
| `stores/designStore.ts` | 57 |
| … (41 more files) | |
| **Total, live** | **2,066 raw → ~1,450 translatable** |

The dead files add 3,275 raw strings.

- **Caution:** seed strings in `designStore.ts`, `BlocksPanel.tsx` and `suggestedReqs.ts` are **persisted** to the backend as element
  and requirement names. Translating them changes stored data, not just display.

### 6.2 Backend user-facing strings

About 4,700 prose literals across `packages/*/src`, excluding tests, docstrings and logging.

- **HTTP errors:** 181 `HTTPException(` calls (top files: `routers/functions.py` 19, `lifecycle.py` 18, `elements.py` 16,
  `exports.py` 12). The frontend shows `detail` verbatim in `workbench/AnalysesPanel.tsx:126` and `components/ConflictsPanel.tsx:34`.
- **Analysis and closure text** shown in panels: `services/session_guidance.py` (89), `constraint_propagation.py` (99),
  `fmeca_closure.py` (76), `physics_closure.py` (61), `requirement_engine.py` (56), `mission_trade.py` (139), `regulatory.py`
  (178), `launch_planner.py` (89), `ground_configurator.py` (53).
- **Model and catalog text:** `spacecdf_common/models/architecture.py` (402), `models/decisions.py` (68), `models/interfaces.py`
  (48).
- **ECSS / document export templates** (`routers/exports.py`, 2,516 lines, 12 export routes l.641-2487):
  - `spacecdf_agents/exporters/docs/templates/{srr,pdr,cdr}.md.j2`: 3 Jinja Markdown templates, 2,193 words.
  - `exporters/docs/docx_generator.py` (123 literals), `theme.py`, `figures.py`, `xlsx_generator.py`.
  - `spacecdf_server/services/docx_generator.py` (276), `did_generator.py` (189), `semp_generator.py` (168),
    `compliance_generator.py`.
  - Inline report prose in `exports.py` itself (261: launch-ICD, RSSSA, deorbit, thermal report, test plan).
  - `exporters/fsw/generator.py` (113), `exporters/smo/exporter.py` (56).
  - This is about 1,300 strings in all. Recommend an additive `?lang=` on export routes with a per-language template directory or
    gettext catalog. A separate decision is whether French ECSS deliverables are wanted at all.
- **LLM agents:** `spacecdf-ai` capabilities load system prompts from `src/spacecdf_ai/prompts/*.txt` (13 files) via
  `BaseCapability.get_system_prompt()` (`capabilities/base.py:35`). `execute()` (l.70-103) has no language input, and
  `OutputConfig.language` is never read. **Yes, they need a language parameter.** Thread `language` from the `/api/ai/*` request
  body (`routers/ai.py:82 /ask`, `:176 /critique-need`, `:186 /write-requirements`, `:196 /review-design`) or from config into
  `execute()`, and append "Respond in French (Canadian)" to the system prompt. The prompt files themselves do not need translating.
  The deterministic `spacecdf-agents` tier-1/2 agents (`power.py`, `thermal.py`, `tier2/conflicts.py` 45 …) emit English
  `rationale`/`assumptions` that also flow into exports.
- **CDF tests asserting English backend text:** `tests/test_services/test_vv_closure.py:78-95` (exact acceptance-criterion
  strings), `test_mission_design_scenario.py` (21), `test_exporters/test_capella.py` (19), `test_ecss_10_25.py` (10),
  `test_api/test_analyses_ground_api.py` (15), `test_services/test_fmeca_closure.py:82`, `test_physics_closure.py:107`. The
  frontend has no tests. Backend text must therefore default to English.

---

## 7. Estimates and work-packet split

### 7.1 String totals

| Component | UI strings to translate |
|---|---|
| MCS (index.html ~85 + mcs.js ~575 + schematics ~25) | ~685 |
| Planner (index ~85 + planner.js ~150 + wide.html ~20 + wide.js ~50) | ~305 |
| Instructor (index ~110 + instructor.js ~110) | ~220 |
| RF sim (index ~80 + sim ~55) | ~135 |
| Shared design system (components.js ~25 + format.js ~6) | ~30 |
| **SMO UI subtotal** | **~1,375** |
| CDF frontend (live files only) | ~1,450 (+~2,300 if dead files are kept) |
| **UI total** | **~2,800** |

Separate content tracks, not UI strings:

- **SMO config catalogs:** about 2,600 YAML prose strings, ~17k words. That covers parameters, TC catalog, events, S12/S19, FDIR,
  procedure index, mcs/*.yaml, failure codes, failure specs and scenarios.
- **SMO Markdown:** procedures (92k words) and manual (70k words).
- **CDF backend:** about 4,700 literals, of which about 1,300 are ECSS/doc export text.

### 7.2 Packet plan

There are two serial prerequisites, then eight parallel packets. No two packets edit the same file. Each translation packet owns
its own dictionary file(s).

**Prerequisites (one agent each, land first):**

- **S0 — SMO i18n infrastructure.**
  - New `smo-common/.../ui/i18n.js` (`t()`, `getLang()`, `applyStaticI18n()` for `data-i18n` and attribute variants).
  - New `ui/i18n/fr.json`.
  - Translate `components.js` and `format.js` (additive `fmtNum` / unit words).
  - Update `tests/test_mcs/js/modern_harness.js` to copy and rewrite `i18n.js`.
  - Add the `lang` default to `/api/client-config`, `/api/config/planner`, instructor `/api/state` and rfsim `/api/config`, plus
    `schemas.py lang:` / `SMO_LANG` / `--lang`. JSON fields only, no routes.
  - Add a dictionary-completeness test.
  - About 30 strings.
- **C0 — CDF i18n infrastructure.**
  - `src/i18n/` (tiny `t()` hook plus `fr.json` loader; no new dependency needed).
  - `lang` in `uiStore.ts` with a `localStorage` key `spacecdf-lang` and `?lang=`.
  - EN/FR toggle in `App.tsx` header; translate `App.tsx`.
  - Locale-aware `fmtNum`.
  - Thread `language` through `spacecdf-ai` `BaseCapability.execute()` and `routers/ai.py`.
  - About 30 strings plus plumbing.

**Parallel translation packets (each edits only the files listed, plus its own `*.fr.json`):**

| # | Files owned | Est. strings |
|---|---|---|
| S1 | `smo-mcs/.../modern/mcs.js` (one file, too large to split safely; sections 2-19) → `modern/i18n/mcs.fr.json` | ~575 |
| S2 | `smo-mcs/.../modern/index.html`, `schematics.svg` (prose labels only) → `modern/i18n/mcs-shell.fr.json`; `smo-rfsim/.../modern/index.html`, `sim.html` → `smo_rfsim/static/modern/i18n/rf.fr.json`. Watch the rfsim token gates. | ~245 |
| S3 | `smo-planner/.../modern/index.html`, `planner.js`, `wide.html` (incl. CSS `content:"STALE"`), `wide.js` → `modern/i18n/planner.fr.json` | ~305 |
| S4 | `smo-simulator/.../instructor/static/modern/index.html`, `instructor.js` (incl. `?lang` propagation like `?ui`) → `modern/i18n/instructor.fr.json` | ~220 |
| C1 | CDF shell, wizard and decisions: `workbench/{LevelWorkbench,MissionWizard,ReadinessChecklist,EscalationBanner,PresenceBar,DecisionPanel,DesignTools}.tsx`, `components/{MarginTower,OptionSwitcher,OptionCompare,ErrorBoundary}.tsx`, `ai/*.tsx` | ~350 |
| C2 | CDF blocks, guidance and export: `workbench/{BlocksPanel,BlockDiagram,EquipmentBrowser,GuidancePanel,ExportPanel}.tsx`, `components/ExchangePanel.tsx`, `stores/{designStore,modelStore}.ts`, `types/arcadia.ts` (decide display-only vs persisted seed names) | ~470 |
| C3 | CDF requirements, V&V and interfaces: `workbench/{VVPanel,RequirementsPanel,InterfacesPanel,suggestedReqs}.ts(x)`, `components/{VVPlanPanel,ICDTable,TraceabilityTree,FMECAPanel,FunctionTree}.tsx` | ~350 |
| C4 | CDF analyses and budgets: `workbench/{AnalysesPanel,BudgetPanel}.tsx`, `components/{PhysicsClosurePanel,GroundSegmentPanel,MissionSimulationPanel,ParameterPanel,ConflictsPanel}.tsx`, `charts/SVGLineChart.tsx` | ~270 |

**Optional later packets:**

- **K1:** SMO config overlays `configs/eosat1/i18n/fr/*.yaml`, keyed by id, plus a client lookup. Can be split by catalog.
- **K2:** SMO Markdown procedures and manual (document translation).
- **K3:** CDF backend export templates and generators with `?lang=`.
- **K4:** CDF backend analysis and guidance messages.

Each touches a disjoint file set from S1-S4 and C1-C4.

**Agent rules to include in every packet:**

- English stays the default and the dictionary key. en rendering must remain byte-identical.
- Never touch classic pages or add routes.
- Do not translate mnemonics, PUS labels, mode or state names, hex ids or units.
- Keep `.` decimals in engineering values unless the owner rules otherwise.
- Avoid "POSTE" and "impair" in `smo-rfsim/static/modern/index.html`.
- Run the UI test set and compare with the baseline in §0.3.
