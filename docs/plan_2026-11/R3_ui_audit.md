# R3 — UI/UX audit of the C2O platform (SMO suite + SpaceCDF)

*Audit date 2026-10-30, against `/home/claude/c2o` at `558b202`. The repo was not changed. Screenshots are in `screens/` (112 PNGs). Raw measurements are in `sim_metrics_all.json` and `cdf_metrics.json`, next to this file.*

---

## 0. Method and run conditions

| Item | Detail |
|---|---|
| Apps run | `sim/start.sh` (all profile): simulator/instructor :8080, MCS :9090 (modern, plus `/classic`, `/dumps`, `/reports`), planner :9091 (and `/wide`), delayed-TM viewer :8092, orbit tools :8093, doc viewer :8095, scenario generator :8096, ADCS viewer :8097. SpaceCDF backend :8000 and Vite dev frontend :5173. **The radio (:8094) was not captured**, because the brief said to capture it only when the suite starts with `--rf`. |
| Start-up note | `sim/.venv/bin/activate` hard-codes `VIRTUAL_ENV=/home/claude/work/smo/.venv` (it was copied from an old checkout), so `./start.sh` ran the stale packages and crashed on a TTCConfig schema error. I ran a scratch copy of `start.sh` that put `sim/.venv/bin` on PATH. This is an environment problem, not a UI one, but it will hit anyone who copies the venv. |
| Sim state for screenshots | Phase 6 (nominal). HK SIDs 1–12 were enabled through MCS `/api/pus-command` (S3,5). `override_passes` was on. `eps/undervoltage` was injected to get realistic alarms. Captures were taken at **60×** (most screens) and **1×** (the position screens, for live values). |
| Viewports and languages | 1440×900 and 390×844. EN and FR wherever a language switch exists (`?lang=fr`). |
| Tools | Playwright/Chromium. **axe-core 4.10.2** injected (WCAG 2.0/2.1/2.2 A+AA tags). A computed-style scan recorded font-size distribution, clipped text and horizontal overflow. A 25-stop Tab walk checked focus visibility. Network timing used the Performance API. Code was inspected for root causes. |
| SpaceCDF data | Example mission → L0 preset "CubeSat LEO Mission" → drill into Mission → Space Segment → L2 preset "Standard Spacecraft Bus" → Run Analysis. The "Space Segment" drill failed in FR because the node label is translated ("Segment spatial"), so the FR captures stop at L1. |
| Side effects | The SMO start-up regenerated `sim/workspace/audit/procedure_audit.{html,json}`; I reverted both with `git checkout`. About 8 new studies were written to `design/spacecdf.db`, which is git-ignored. Every process I started was stopped by process group, and ports 8000, 5173, 8080–8097, 9090 and 9091 were confirmed free. |

---

## 1. Scorecard per app

| App | Stack | Shared DS? | axe (AA) | Text <12 px | 390 px overflow | FR | Notes |
|---|---|---|---|---|---|---|---|
| MCS modern | vanilla ES modules; `mcs.js` 260 KB | yes (`/static/shared/`) | 1 rule, critical (nav-rail ARIA); **0 contrast** | 13–135 nodes per page (SVG schematic text at 10 px) | +583–668 px | complete (0 missing keys at runtime) | Strong base, built on PRINCIPLES.md P1–P10 |
| Planner modern | vanilla | yes | 1 critical (unlabelled select) | 0 | none (stacks) | complete | Good |
| Planner `/wide` | vanilla | yes | 0 | 0 | n/a | layout collisions | FR overlaps |
| Instructor modern | vanilla | yes | 2 critical (row roles), 1 serious | 0 | +590 px | complete | Truth panel clear; speed buttons stop at 10× while the API allows 60× (none highlighted) |
| MCS classic | 664 KB single HTML | no | 58 contrast nodes, 46 ARIA, 9 px text | 274 nodes | – | EN only (by ruling) | Kept for compatibility |
| `/dumps`, `/reports`, `/config` | server-inline HTML | no | – | `/config`: 115 nodes, 136 clipped cells | – | EN only | Out of scope of the Aug redesign |
| Delayed-TM viewer :8092 | Python-embedded HTML | no (navy palette, JetBrains Mono) | 2 label (critical) | 14 | – | EN only | Shows the server filesystem path |
| Scenario generator :8096 | Python-embedded | no (GitHub-dark) | label + select-name | 0 | – | EN only | – |
| Orbit tools :8093 | Python-embedded | no (**light theme, Courier New**) | html-has-lang | 0 | – | EN only | Visually from another product |
| ADCS viewer :8097 | Python-embedded | no | 16 label, contrast 2.32:1 | 31 | – | EN only | – |
| Doc viewer :8095 | Python-embedded | no | 0 | 0 | – | chrome EN; lists FR docs under an "I18N" category | – |
| SpaceCDF | React 19 + Vite, 32 kLOC TSX, **3,570 inline `style={{}}`** | no (own 11 vars, Tailwind-grey palette) | contrast (1.14:1, 3.65:1, 3.67:1), select-name, target-size (24 nodes) | **78–95 % of text nodes; min 9 px** | +395–480 px | ~1,100 keys, 44 gaps, **281 hard-coded English JSX phrases** | 0 `@media` rules |

**What works.** These strengths should be kept and spread to the other apps:
- The modern SMO consoles have zero contrast violations. Their tokens are machine-validated to 7:1 (see `design-system.css` header).
- Every MCS and instructor tab stop shows a visible focus ring, and skip links exist.
- The F6 region cycle and the `a`/`k`/`?` shortcuts work.
- A greyscale acceptance mode exists, and the four-question SA header is in place.
- FR runtime coverage on the consoles is complete.
- The MCS keyboard walk was 25/25 with focus rings.

---

## 2. Top 15 UI problems (ranked by severity × frequency)

Severity scale: S4 = misleads an operator or blocks a task; S3 = slows the task or causes errors; S2 = friction; S1 = cosmetic. Frequency scale: F4 = every screen or session; F1 = rare.

| # | Problem | S×F | Evidence | Concrete fix |
|---|---|---|---|---|
| **1** | **The MCS "What's next?" card and the Overview pass table always say "no pass schedule"**, while the timeline directly above shows passes. Root cause: `/api/displays/contact-schedule` returns `next_passes`, but `mcs.js:4921` reads `d.passes \|\| d.contacts \|\| d.schedule`. One of the four SA questions is permanently blank. | 4×4 | `mcs_ovr_d_en.png`, `mcs_pos_*` (header) | Read `d.next_passes`. Add a contract test that the client field list matches the server response. In the longer term, generate types from one schema (see §3.4). |
| **2** | **Alarm flood is not managed.** One injected `undervoltage` produced 31–42 alarms, all P2, with repeats (e.g. "Battery Cell Failure" ×6). Rows read like "EPS — (0.10)", with no parameter, limit or direction. The ACK button overlaps the text on wrapped rows (AOCS row). Counts disagree across the page: header "34 ALARMS", FDIR page "Active alarms 0", FDR rail badge "34". | 4×4 | `mcs_alarms_d_en.png`, `mcs_fdir_d_en.png` | Row template `[P#] PARAM-NAME value unit ▲ limit (soft/hard) · age · procedure`. De-duplicate by (param, condition) with a ×N counter and last-occurrence time. Group consequential alarms under their first-out (root) alarm by default. Show the rate meter with the ISA-18.2 flood threshold (>10 per 10 min). Derive every count from **one** alarm store, as PRINCIPLES P7.5 requires. |
| **3** | **Stale and never-received values both render as "—" on a hatch.** The last-known value disappears. At training speed-up most of the console turns into hatch and em-dashes ("STALE · 59 s" while "LINK · IN CONTACT"). At 1× the same screens are full of values. | 4×3 | compare `mcs_ovr_d_en.png` (60×) with `mcs_pos_eps_tcs_d_en.png` (1×); `mcs_pos_aocs_d_en.png` | Keep the last value, dimmed to `--tx3` italic, with an age chip (`82.1 % · 59 s`). Reserve the em-dash for "never received", shown as a distinct "no data" label. Scale the stale thresholds by downlink capacity and sim speed, or show a "link-limited at x60" banner. Apply the hatch to the value cell only, never the whole card. |
| **4** | **SpaceCDF text is too small.** 78–95 % of text nodes are under 12 px, the minimum is 9 px (`0.55rem`), and analysis cards use ~9.6 px italic. Classroom projection and the online course make this worse. | 3×4 | `cdf_03_tab_analyses_d_*.png`, `cdf_05_vv_gates_d_en.png` | Set a 12 px floor (≥14 px for values). Run a codemod that maps every `fontSize: '0.5x–0.7x rem'` to a type-scale token. Add an ESLint rule that bans `fontSize` literals. |
| **5** | **SpaceCDF contrast failures.** "Load Example Mission" is `#8B0000` on `#1f2937` (≈1.9:1, practically invisible on the home screen). Unvisited level tabs are 1.14:1. The EN/FR active pill is white on `#3b82f6` at 11.5 px (3.67:1). The purple active tab is 3.65:1. React-Flow zoom controls are unthemed white squares. | 3×4 | `cdf_01_home_d_en.png`, `cdf_02c_after_run_d_en.png` (bottom-left) | Move to the shared tokens (§4). Use `colorMode="dark"` on `<ReactFlow>`. Use `--info` on `--s1` for active states. Use proper `disabled` styling plus `aria-disabled` for unvisited levels. |
| **6** | **SpaceCDF layout is fixed and not responsive.** There are zero media queries. The bottom activity panel is fixed at 280 px: `const [panelHeight] = useState(280)` has no setter, so it cannot be resized. At 1440×900 the budget table shows 5 rows under a half-empty diagram. At 390 px the page overflows by 395–480 px. | 3×4 | `cdf_03_tab_budget_d_en.png`, `cdf_02_workbench_blocks_m_en.png` | Add a draggable split, persisted per user. Collapse the diagram to a strip when a table tab is active. Use a single-column layout under 900 px. |
| **7** | **The platform looks like 8 products.** The modern consoles use the shared DS. The tools use five ad-hoc palettes: navy + JetBrains Mono, GitHub-dark, **light + Courier New**, ADCS dark, doc-viewer dark. SpaceCDF uses Tailwind greys with a dark-red brand. Headers, naming ("Delayed TM viewer" :8092 vs "Delayed TM archive" `/dumps`) and navigation differ, and no page links to its siblings. | 3×4 | `orbittools_d_en.png`, `delayedtm_d_en.png`, `scenariogen_d_en.png`, `adcsviewer_d_en.png`, `mcs_dumps_d_en.png`, `cdf_01_home_d_en.png` | Adopt the shared DS and app bar everywhere (§4–§5). Merge the two delayed-TM pages. |
| **8** | **Tool pages are English-only and partly inaccessible.** `?lang=fr` is ignored on :8092/:8093/:8096/:8097 and on `/dumps`, `/reports` and `/config`. axe found unlabelled inputs (16 on the ADCS viewer) and no `lang` attribute on orbit tools. The doc viewer exposes the `i18n/` folder as an "I18N" category and lists French docs first to English users. | 3×3 | `*_d_fr.png` for the tools, `docviewer_d_en.png` | Serve `i18n.js` and `design-system.css` from each tool server (they are Python and can mount `smo_common/ui`). The doc viewer should pick the document language from the UI language and hide `i18n/`. |
| **9** | **The consoles are unusable below about 1000 px.** The MCS header takes 350 px of a phone screen. SA answers truncate ("LIVE …", "LIAIS…"). Rail badges overlap rail labels (`EPS●1`). The MCS overflows by 583–668 px and the instructor by 590 px. This matters for the web and practice modes on laptops and tablets. | 3×3 | `mcs_ovr_m_*.png`, `instructor_m_fr.png`, `mcs_pos_aocs_m_en.png` | Set a declared minimum of 1280 px for operating positions, with a clear notice. Under 1000 px, offer a read-only **"monitor view"**: a two-row header, the rail turned into a bottom bar, and cards stacked. Move rail badges to a corner pip outside the label box. |
| **10** | **State indicators contradict each other.** The header says "LINK · IN CONTACT" while the Overview says "NO CONTACT" and the wall display says "HORS CONTACT". The header says EMERGENCY while FDIR says "LATCHED SAFE". Each panel derives link and mode from a different field (`state.in_contact`, the override, TM). | 4×2 | `mcs_ovr_d_en.png` (top vs right), `planner_wide_d_fr.png`, `mcs_fdir_d_en.png` | Add one selector module (`smo_common/ui/state.js`: `linkState()`, `modeState()`, `freshness()`) used by every panel and console. Show the provenance sub-label everywhere, which is already the rule for mode. |
| **11** | **Cross-origin calls from MCS to the planner fail.** The page is served from `localhost:9090` but calls `planner_url=http://127.0.0.1:9091`, and CORS blocks it. This breaks the burn-plan confirmation (propulsion page) and the ground-station load on the classic page. | 3×2 | console errors in `sim_metrics_all.json` (`mcs_pos_propulsion`, `mcs_classic`) | Proxy the planner same-origin through MCS (`/planner/api/...`), or derive `planner_url` from `location.hostname`. The portal reverse proxy (§5) removes the problem class. |
| **12** | **Commanding and procedure affordances ignore state and hazard.** START, PAUSE, RESUME, STEP, SKIP and ABORT are all enabled with nothing loaded. The svc/sub/data-hex fields have placeholders but no labels. More than 60 quick-command buttons sit in a flat grid where "RW0 arrêt" or "Refroid. FPA arrêt" look as benign as "Nominal". The S3 buttons stay English in FR ("ENABLE (3,5)"). | 3×3 | `mcs_proc_d_en.png`, `mcs_cmd_d_fr.png` | Enable buttons from a procedure state machine. Use visible labels. Classify commands (routine / critical / hazardous, as in the ECSS-E-ST-70-31 command criticality attribute) and give critical ones an **arm → execute** two-step with a distinct border. Group them by subsystem with collapsible sections and a filter. |
| **13** | **The French layout breaks on the wall display.** The "ORBITE SUIVANTE … DÉDUITE DE" label collides with the TROLL pass label. ÉCLIPSE/CONTACTS/ACTIVITÉS row labels stack over each other. Headings truncate ("ADÉQ. PASS…", "SoC EN SORTIE …", "· A…"). | 2×3 | `planner_wide_d_fr.png`; minor clipping in `mcs_*_fr` (3 clipped elements vs 2 in EN) | Add label collision avoidance on the canvas timeline. Allow two-line headings. Lay out against FR strings, which run 20–30 % longer, as the design case. Add an FR screenshot test. |
| **14** | **SpaceCDF information architecture is confusing.** Level names don't match their content: "1: Systems (Mission)" shows *segments*, and "2: Subsystems (Space Segment)" shows subsystems. Unvisited levels look disabled but are clickable buttons. Eight rainbow subsystem hues (red Thermal, orange Propulsion) read as alarms next to the SMO grey-is-nominal rule. The Budget Rollup indents Payload…Propulsion under *Operations* and shows Space Segment mass "—" while the Mission total is 21.87 kg. The gate review shows "NOT READY" in red with "Fail: 0". There are 64 native `alert/confirm/prompt` calls; the example-mission picker is a `window.prompt` asking for a number. | 3×3 | `cdf_02a2_level1_segments_d_en.png`, `cdf_02c_after_run_d_en.png`, `cdf_04_vv_d_en.png`, `cdf_05_vv_gates_d_en.png` | Use ECSS product-tree names (Mission → Segment → System/Element → Subsystem → Equipment). Make subsystem identity a low-chroma categorical palette plus a letter badge, never red or amber. Fix the rollup parent attribution. Use amber "NOT READY (n manual/advisory)" and reserve red for any failed check. Replace native dialogs with a `Dialog` component and use a card picker for examples. |
| **15** | **ARIA and semantics are off.** The MCS nav rail is `role=tablist` with separator children: axe *critical* on every MCS page, and the rail costs 14 tab stops with no roving tabindex. Instructor event rows use `role=row` without a table. The planner has seven buttons all named "SCHEDULE". SpaceCDF has 7 `aria-*` attributes and 4 `role`s in 32 kLOC, plain-button tabs, and no focus trap in modals. | 2×4 | axe output (`sim_metrics_all.json`, `cdf_metrics.json`); `kbd_*_tab7.png` | Use `role=none` on rail separators (or move them out of the tablist), roving tabindex with arrow keys, `aria-label="Schedule <activity>"`, and real `table` semantics. In CDF, use shared `Tabs`/`Dialog` primitives with ARIA built in. |

**Also noted, outside the top 15.**
- The MCS light theme leaves the ground-track map dark (`mcs_light_d_en.png`).
- Unit "C" is shown instead of "°C".
- Parameter mnemonics (`eps.bat_soc`) are the primary label on Key Parameters, with the human name hidden.
- The AGE and "NO LIM" cells wrap to two lines in the parameter table.
- In the instructor, OBC truth "TRUE OFFSET −840499199.877 s" wraps mid-number.
- The instructor's 10 px event-log header and 200 px drawer cut panels off.
- The delayed-TM page and `/dumps` print the absolute server path (`/home/claude/c2o/sim/workspace/dumps`). That is a minor information leak once the suite is web-hosted.
- The rail labels themselves (OVR/AOC/PRP/OBD…) are three-letter codes with no expansion until hover.

---

## 3. Root causes in the code

### 3.1 SMO: the shared DS stops at the three consoles
- `smo_common/ui/` holds `design-system.css` (21 KB, validated tokens), `components.js`, `format.js`, `glyphs.svg` and `i18n.js`. It is served at `/static/shared/` by **MCS, the planner, the instructor and the rfsim modern pages only**.
- The five tool servers in `sim/tools/*.py` embed their own HTML and CSS: delayed TM has 22 distinct hex values, the scenario generator 30, the ADCS viewer 15, orbit tools 8 (light), and the doc viewer 7. None loads the shared DS or `i18n.js`.
- MCS `/dumps`, `/reports` and `/config` are server-inline pages. The August delivery notes list them as "out of scope, keep old look".
- Each modern console still carries **9.5–13.7 KB of page-local `<style>`**, and `mcs.js` emits **188 inline `style=` strings**. The shells differ: MCS has a rail and SA strip, the planner a top bar only, the instructor a banner and three columns. So header, nav and drawer patterns are re-implemented three times.
- `mcs.js` is a 260 KB, 20-section monolith with untyped JSON access (`d.passes || d.contacts || d.schedule`). Field-name drift is invisible until a screen is blank (problem 1).
- State derivation (contact, mode, alarm counts, freshness) is written per panel, which produces the contradictions in problems 2 and 10.

### 3.2 SpaceCDF: no system at all, just inline styles
- `index.css` defines 11 variables (`--bg-primary … --info`, Tailwind grey/blue values). The TSX has **~3,000 hex literals (53 distinct)** and **3,570 `style={{}}` objects**, against roughly 1,300 `var(--…)` uses.
- There are no primitives (no `Button`, `Tabs`, `Card`, `Table`, `Dialog`). Instead there are 24 ad-hoc style constants (`wizBtn`, …) and 456 `className`s for a 272-line stylesheet.
- There are zero `@media` rules and no density or theme switch. Light mode does not exist.
- **39 of 110 component files are not imported by the live tree** (e.g. `TemplateGallery`, `Phase0–5*`, `PowerRailEditor`, `DesignWorkspace`, `UserManual`). They still count in the i18n surface and in the 281 hard-coded English JSX phrases.
- `window.alert/confirm/prompt` appears 64 times. The production build is a single **991 KB JS chunk (280 KB gzip)** with no code splitting.

### 3.3 Two token vocabularies for the same concepts

| Concept | SMO token / value | SpaceCDF token / value |
|---|---|---|
| ok / success | `--ok #00C896` (verdicts only) | `--success #10b981` (used freely) |
| caution | `--warn #F0B429` | `--warning #f59e0b` |
| alarm | `--alarm #FF7B72` | `--danger #ef4444` |
| interaction | `--info #6BB3FF` | `--accent #3b82f6` (and `--info #06b6d4`) |
| page | `--bg #0B0D10` | `--bg-primary #0a0e1a` |
| text secondary | `--tx2 #C0C9D4` (10.7:1) | `--text-secondary #9ca3af` (~6.9:1) plus heavy use of `#6b7280` (~4:1 on cards) |

### 3.4 Two i18n runtimes, compatible by accident
- SMO uses its own `i18n.js` (English-text keys, i18next-v4-compatible JSON). Its language key is `smo.lang`.
- SpaceCDF uses i18next. Its language key is `scdf.lang`.
- The catalogs share format and key convention, but there is **no shared glossary**. The same domain words can be translated differently in the two apps, and a user who switches language in one app does not switch the other.

### 3.5 Performance (rough)

| Page | Transfer per load | Requests | DCL (local) | Notes |
|---|---|---|---|---|
| MCS modern EN | ~1.1 MB | 31–38 | 100–200 ms | `chart.umd` 206 KB, `mcs.js` 260 KB (unminified), world map 79 KB; **no gzip, `Cache-Control: no-cache`** |
| MCS modern FR | ~1.4–1.9 MB | 35–45 | similar | plus `fr.db.json` 266 KB |
| Planner / instructor | 0.3–0.95 MB | 21–27 | ~100 ms | – |
| SpaceCDF (prod `dist`) | 991 KB JS + 19 KB CSS (280 KB + 4 KB gzip) | – | – | Dev server measured 5 MB; not representative |

All of this is fine on a LAN. Over `c2o.live` with no compression or caching, every console reload costs about 1–2 MB. aiohttp gzip middleware plus content-hashed, `immutable` static assets would cut that by about 70 %.

---

## 4. A unifying design system ("C2O DS")

The principle is **one token source, two themes and two densities, no build step for the consoles**. The SMO DS is the better-founded base (validated contrast, ISA-101/P1–P10), so grow it into the platform DS rather than starting over.

### 4.1 Token tiers
1. **Primitive**: neutral ramp `n0…n12`, status ramps (amber, red, blue, green, violet), categorical ramp `c1…c8` (low chroma).
2. **Semantic**: the names apps use. These are listed below.
3. **Component**: e.g. `--btn-bg`, `--chip-alarm-fg`. They are derived from semantic tokens only.

Author the tokens in **DTCG JSON** (`ui/tokens/*.json`). A short generation script emits `tokens.css` (custom properties under `:root`, `[data-theme]` and `[data-density]`) and `tokens.ts`, and commits both (no runtime build). A test fails if the generated files drift from the JSON.

### 4.2 Semantic colours

| Token | Dark control-room (default for ops) | Light (CDF / classroom / projector) | Rule |
|---|---|---|---|
| `--surface-0/1/2/3` | `#0B0D10 / #14171C / #1C2129 / #262C36` | `#F4F5F7 / #FFFFFF / #EEF0F3 / #E3E6EA` | Panels lift by luminance, not hue |
| `--line / --line-strong` | `#2B313A / #3B4450` | `#D5D9DE / #B8BEC6` | Decorative only |
| `--text-value` | `#F5F7FA` | `#0B0D10` | Telemetry numerals, brightest |
| `--text / --text-2 / --text-3` | `#E9EDF2 / #C0C9D4 / #9BA7B4` | `#141619 / #383C42 / #4A4F56` | ≥7:1 dark, ≥4.5:1 light |
| `--interactive` | `#6BB3FF` | `#15477C` | Focus, links, selection, commanded state. Never data |
| `--status-caution` | `#F0B429` | `#6E4300` | Soft limit, P3, advisory |
| `--status-alarm` | `#FF7B72` | `#8F1D12` | Hard limit, P1/P2, failed check |
| `--status-ok` | `#00C896` | `#0B5A42` | Explicit verdicts only (GO, PASS, lock) |
| `--status-shelved` | `#A79BF8` | `#453A96` | Shelved / suppressed |
| `--status-stale` | `#7E8697` (graphics only) + hatch | `#53575D` | Never text colour |
| `--status-sim` | dashed `--interactive` border | same | TRAINING / SIM chip, instructor truth |
| `--cat-1…8` (CDF subsystem identity) | e.g. `#7FA7C9 #9C8FD1 #6FB7A8 #B7A07A #8FA3B8 #C2879E #7FB38A #A7A7A7` | darker equivalents | Low chroma, **never red or amber**, always paired with a letter badge |

### 4.3 Limit and alarm presentation
This follows the ISA-101/18.2 model already in PRINCIPLES P1, P3, P4, P6 and P7, extended to SpaceCDF margins:

| State | Value text | Cell / row | Glyph | Motion |
|---|---|---|---|---|
| Nominal | `--text-value` | none | none | none |
| Soft limit / caution / P3 | `--status-caution`, bold | 2 px left bar plus wash | ◆ | none |
| Hard limit / P1–P2 | `--status-alarm`, bold | 2 px bar, wash, row border | ▲ (P1 filled) | blink only while P1 is unacknowledged |
| Stale | last value in `--text-3` italic plus age | hatch on the cell | ◷ | none |
| Never received | "no data" in `--text-3` | none | ∅ | none |
| Shelved / suppressed | `--status-shelved` | dashed border | ⧗ | none |
| Verdict PASS/GO | `--status-ok` | none | ✓ | none |

The same rules apply to **SpaceCDF margins**: margin < 0 is alarm, margin < the ECSS-E-HB-10-02/MIL-STD-1540-style target is caution, and margin met stays neutral. Green appears only for a *gate verdict*.

### 4.4 Type, spacing, density
- **Type.** Sans: Inter / system-ui for labels. Mono: JetBrains Mono, falling back to Consolas/Menlo, with `font-variant-numeric: tabular-nums` for values. Ship the fonts with the suite (no CDN, so it works offline). Scale: 12 / 13 / 14 / 16 / 20 / 24 / 32, plus a wall scale of 18–64. **The floor is 12 px**, primary readouts are ≥14 px and wall text ≥18 px. Enforce this with a stylelint/ESLint rule.
- **Spacing.** 4 px base: 4 / 8 / 12 / 16 / 24 / 32 / 48. Radius 4 / 6. Use `data-density="console"` (row 28 px, 8 px gaps) for SMO and `"comfortable"` (row 36 px, 12–16 px gaps) for SpaceCDF and the docs.

### 4.5 Components
These become one catalogue, with the same names in CSS classes, vanilla helpers and React wrappers:
- `AppBar` (app switcher, mission, clocks, lang, theme, help) and `NavRail`/`Tabs`
- `Panel` (card), `DataTable` (sticky header, numeric alignment, column priority for narrow widths) and `ValueCell` (value + unit + limit bar + age + provenance)
- `StatusChip`, `AlarmRow`/`AlarmList` and `Banner` (contingency / training)
- `Button` (primary, secondary, quiet, danger, **armed two-step**) and `Field` (label, help, error; no placeholder-only inputs)
- `Select`, `Drawer`, `Dialog` (to replace `alert/confirm/prompt`), `Toast`, `EmptyState`, `Kbd`, `LangToggle`, `ThemeToggle`
- `Timeline` (passes, eclipse, activities, with label collision avoidance), shared by the MCS, planner, wall display and CDF ConOps.

---

## 5. Sharing it between vanilla consoles and React SpaceCDF, and the portal question

### 5.1 Sharing mechanism (recommended)
1. **Canonical home: `sim/packages/smo-common/src/smo_common/ui/`.** It is already package data, already served at `/static/shared/` with no symlinks, and its tests already sha-gate it. Promote it to a top-level `ui/` only if the Docker build contexts allow; otherwise leave it where it is.
2. **Tokens and CSS** are the contract: `tokens.css` plus `c2o.css` (component classes `.c2o-btn`, `.c2o-panel`, …). Consoles `<link>` them. SpaceCDF imports them through a Vite alias, `@c2o/ui → ../../sim/packages/smo-common/src/smo_common/ui`, and its Dockerfile copies that folder.
3. **Behavioural components as standard custom elements** (`<c2o-value>`, `<c2o-alarm-list>`, `<c2o-appbar>`, `<c2o-timeline>`), written in plain ES modules with no Lit and no build. **React 19 supports custom elements natively** (properties and events), so SpaceCDF can use them directly. The vanilla consoles need nothing new.
4. **React-only primitives** (`Button`, `Tabs`, `Dialog`, `DataTable`) are thin wrappers that only apply the shared classes and ARIA patterns. That keeps one visual definition in CSS.
5. **i18n**: one shared glossary catalog (`ui/i18n/glossary.<lang>.json`) for domain terms, loaded by both runtimes. Use one language key, `c2o.lang`, and keep reading the old `smo.lang`/`scdf.lang` for one release.
6. **Guard rails**: lint rules that ban hex literals and `fontSize` in TSX and in console JS (allow-listed in `tokens.*` only). Add Playwright visual tests at 1440×900, 1280×720, 1024×768 and 390×844 in EN and FR, plus axe in CI.

### 5.2 Should a portal shell host both? Yes, as a thin shell, not an iframe SPA
- The web architecture (`sim/docs/web_2026-10/ARCHITECTURE.md`, WP-2) already plans a portal for auth, missions, teams and the session launcher. Make it the **UI front door** too: launcher tiles, role-based app list, preferences (language, theme, density) and help/docs.
- It should also be the **same-origin reverse proxy** (`/mcs/`, `/planner/`, `/instructor/`, `/cdf/`, `/docs/`, `/tools/…`). That removes the CORS failure class (problem 11), gives one cookie for language and identity, and lets 2FA sit in front of everything.
- **Do not wrap the consoles in iframes inside a SPA.** Operators need full-screen, multi-monitor, one-console-per-window layouts, and `/wide` is a wall display. Instead, every app renders `<c2o-appbar>` (32 px) with the app switcher, session, lang and theme, and the portal owns navigation between apps.
- The scenario generator, orbit tools, ADCS viewer and delayed-TM tools should become "Tools" pages inside the portal chrome, restyled with the DS.

---

## 6. Phased UI plan

### Phase A: quick wins (≤ 2 weeks, about 6–8 dev-days)

| # | Item | Effort | Fixes |
|---|---|---|---|
| A1 | Read `next_passes` in `mcs.js:4921`; add a client/server contract test | 0.5 d | P1 |
| A2 | Same-origin planner calls (proxy or hostname-derived `planner_url`) | 0.5 d | P11 |
| A3 | Alarm row template (param name, value vs limit); ACK overlap fix; ×N de-duplication; one derived count | 1.5 d | P2 (partly) |
| A4 | Stale = last value dimmed plus age; distinct "no data" state | 1 d | P3 |
| A5 | Procedure buttons enabled by state; labels on override/builder fields; translate the S3 buttons | 0.5 d | P12 (partly) |
| A6 | Nav-rail ARIA (separators out of the tablist, roving tabindex); planner button names; instructor row roles | 0.5 d | P15 |
| A7 | SpaceCDF: codemod to a 12 px floor; fix 4 contrast failures; `colorMode="dark"`; resizable activity panel | 1.5 d | P4, P5, P6 (partly) |
| A8 | aiohttp gzip plus cache headers on all SMO servers | 0.5 d | performance |
| A9 | Doc viewer chooses language and hides `i18n/`; strip server paths from tool pages | 0.5 d | P8 (partly) |
| A10 | `/wide` FR label collisions and two-line headings | 0.5 d | P13 |

### Phase B: medium (1–3 months)
1. **Tokens package** (DTCG JSON → `tokens.css`/`tokens.ts`). Extend `design-system.css` into `c2o.css` with light and dark themes and two densities.
2. **SpaceCDF migration**: Button/Tabs/Panel/DataTable/Field/Dialog primitives; a codemod to remove inline styles and hex values (target <200 inline styles); delete the 39 dead components; replace the 64 native dialogs; ECSS level naming; categorical palette; rollup and gate-verdict fixes; a responsive split layout.
3. **Alarm management per P7**: priorities from rationalisation data, flood meter, first-out grouping by default, shelving with timers, one store feeding every badge.
4. **`smo_common/ui/state.js`** selectors for link, mode and freshness, used by all consoles. Generate JSDoc/TS types from the server responses (pydantic → JSON Schema) and type-check `mcs.js` with `// @ts-check`.
5. **Restyle and translate the tools** with the shared DS and `i18n.js`; merge `/dumps` with the :8092 viewer.
6. **Responsive strategy**: a declared 1280 px minimum for operating positions; a "monitor view" under 1000 px; tablet-safe instructor.
7. **Commanding**: hazard classes from the TC catalogue plus arm → execute for critical commands; grouped and filterable quick commands.
8. **CI**: Playwright visual tests (4 sizes × EN/FR) plus axe at zero critical/serious.

### Phase C: long-term (3–9 months)
1. **Portal shell** (WP-2) with `<c2o-appbar>`, launcher, preferences and the same-origin proxy; fold the tools into it.
2. Split `mcs.js` into page modules and move recurring widgets to `<c2o-*>` custom elements shared with SpaceCDF.
3. **Design-to-ops continuity**: a shared EN/FR glossary; SpaceCDF exports a mission's TM/TC and limits into the MCS display config (P10, "display is configuration"), so students see their own design in ops.
4. Retire the classic UIs once the inventory checklist is fully covered.
5. **Evaluate with users**: scripted pass scenarios with student teams, scored with SUS, NASA-TLX and SAGAT-style SA probes on the four header questions. Compare before and after Phase B, in EN and FR cohorts.

---

## 7. Standards and references applied
- **ISA-101.01 (High-Performance HMI)**: grey/neutral resting state; colour reserved for abnormal; display hierarchy L1–L4. See ["Going Gray: A New HMI Standard" (control.com)](https://control.com/technical-articles/going-gray/) and [ISA-101 colour strategy summary](https://industrialmonitordirect.com/blogs/knowledgebase/isa-101-high-performance-hmi-design-principles-color-strategy).
- **ANSI/ISA-18.2 and EEMUA 191 (alarm management)**: priorities, flood threshold (>10 per 10 min per operator), shelving, first-out. See [IChemE Alarm Management practical guide](https://www.icheme.org/media/16019/icheme-alarm-management-practical-guide-06_05_2021.pdf) and [alarm floods and plant incidents](https://digitalrefining.com/article/1000558/alarm-floods-and-plant-incidents).
- **ECSS-E-ST-70-31C (monitoring and control data definition)**: limit sets (soft/hard), parameter validity and staleness, command criticality / hazard attributes. These drive problems 3 and 12. See [ECSS-E-ST-70-31C](https://ecss.nl/standard/ecss-e-st-70-31c-ground-systems-and-operations-monitoring-and-control-data-definition/).
- **NASA HIDH (NASA/SP-2010-3407) and NASA-STD-3001 Vol. 2 display guidance**: limited colour palette, red/yellow reserved for warning/caution, redundant coding, readable type sizes. See [NASA Color Usage guidelines (Ames)](https://colorusage.arc.nasa.gov/guidelines_specific.php). I took the HIDH content from the handbook as published, not from a fetched copy.
- **WCAG 2.2 AA**: 1.4.3 contrast, 1.4.10 reflow, 1.4.4 resize, 2.4.7 focus visible, 2.5.8 target size, 4.1.2 name/role/value. These were checked with axe-core.
- **EUMETSAT and DLR "mission control display standards".** I found no publicly available document under that name. Their published control-centre practice follows ECSS-E-ST-70-31 and ESA EGOS/EGS-CC conventions, so the ECSS rows above stand in for them. The SMO design study (`sim/docs/design_2026-08/RESEARCH.md`, `PRINCIPLES.md`) already captures ESOC/NASA console practice. This audit mostly measures how far the implementation lives up to those principles.
