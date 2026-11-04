# Logbook and worksheets — shared spec (2026-11-02)

Franz's request: participants log their decisions, thoughts and reflections
as they work, in every tool (MCS, delayed TM, orbit, radio, docs, SpaceCDF,
instructor prep/debrief), with the course workbook worksheets attached in
context. At the end of a session they are prompted to download it. The
server deletes it after 48 hours.

Rulings (Franz, 2026-11-02):
- **Private.** Only the participant reads their own logbook. The instructor
  sees at most counts (entries per seat), never text. Students hand in the
  download if it is to be graded.
- **Retention 48 h.** A person's whole logbook is deleted 48 h after their
  last write (`SMO_LOGBOOK_RETENTION_H`, default 48). A hard cap deletes any
  entry older than 7 days even while the person stays active
  (`SMO_LOGBOOK_MAX_AGE_H`, default 168). Purge runs at start-up and hourly
  in every process that mounts the logbook; it is idempotent.
- Bilingual EN/FR for every string, worksheet text included.

## 1. Identity

`person_id`:
1. Behind IAP: the `X-Goog-Authenticated-User-Email` header, with the
   `accounts.google.com:` prefix removed, lower-cased.
2. Otherwise (laptop, local demo): a cookie `c2o_lb` holding a random
   128-bit id (`local:<hex>`), set `SameSite=Lax; Path=/; Max-Age=30d`,
   `HttpOnly`. Cookies ignore the port, so all local tools on one host share
   it. The UI says "this browser" instead of an email.

The id never leaves the ground segment: smo-link must not carry logbook
traffic (the httpproxy already strips IAP headers; logbook routes are served
locally by each tool, never proxied over the link).

## 2. Storage (one format, two implementations)

Directory: `$SMO_LOGBOOK_DIR`, default `<workspace>/logbook`
(`/opt/smo/workspace/logbook` in containers). On the ground VM every ground
container and `spacecdf` mount the same `ground-workspace` volume, so one
person's entries from every tool land in one logbook.

- One file per person: `<sha256(person_id)[:32]>.jsonl`, mode 0600, dir 0700.
- One JSON object per line (append-only; edits and deletes are appended as
  new records with `op`):

```json
{"v":1,"id":"<uuid4>","op":"add","ts":"2026-11-02T23:41:07.123Z",
 "sim_ts":"2026-03-10T04:18:22Z", "tool":"mcs",
 "kind":"decision", "text":"…",
 "context":{"page":"eps","procedure":"CTG-001","alarm_id":42,"param":"0x0105",
            "study_id":null,"step":null,"position":"eps_tcs","scenario":"…"},
 "worksheet":{"id":"WB-5.5-DB","q":"q3"}, "lang":"en"}
{"v":1,"id":"<same uuid>","op":"edit","ts":"…","text":"…"}
{"v":1,"id":"<same uuid>","op":"delete","ts":"…"}
{"v":1,"op":"downloaded","ts":"…","format":"md"}
```

- `kind`: `decision` | `thought` | `reflection` | `observation` |
  `worksheet` (an answer to a worksheet question; `worksheet` set).
- `tool`: `mcs` | `delayed_tm` | `orbit` | `radio` | `docs` | `instructor`
  | `design` | `portal`.
- `sim_ts` optional (ops tools fill it from sim time when known).
- Writers take an exclusive `fcntl.flock` on the file for append; readers
  fold the records (last edit wins, deletes drop the entry).
- Text limit 8,000 characters per entry; 2,000 entries per person (reject
  with 413 beyond, message tells them to download and clear).
- Purge: delete the file when its mtime is older than the retention; when
  the file is kept, rewrite it without entries older than the max age.
  Also purge `downloaded` markers with the file.

## 3. HTTP API (same paths in aiohttp and FastAPI)

All under `/api/logbook`, same-origin with the tool that serves it. JSON.
No auth beyond identity (IAP already authenticated the request).

| Method | Path | Body / query | Returns |
|---|---|---|---|
| GET | `/api/logbook` | `?tool=&since=` optional filters | `{person:{id_label, local:bool}, retention_h, max_age_h, expires_at, last_write, last_download, entries:[folded entries newest first], count}` — `id_label` is the email or "this browser" |
| POST | `/api/logbook/entries` | `{kind, text, tool, context?, worksheet?, sim_ts?, lang?}` | the entry |
| PATCH | `/api/logbook/entries/{id}` | `{text}` | the entry |
| DELETE | `/api/logbook/entries/{id}` | — | `{ok:true}` |
| GET | `/api/logbook/export` | `?format=md\|html\|json&lang=en\|fr` | file download (`Content-Disposition: attachment; filename="c2o-logbook-YYYYMMDD-HHMM.md"`), records a `downloaded` marker |
| DELETE | `/api/logbook` | — | deletes the person's whole logbook now ("Delete now") |
| GET | `/api/logbook/worksheets` | `?tool=&context=<json>&lang=` | worksheets that apply here (see §4) |

`expires_at` = last_write + retention_h. Export is grouped by session day,
then tool, then time; worksheet answers are grouped under their worksheet
with the question text. The HTML export is print-ready (A4/Letter, the
C2O print stylesheet, readable without the app) so "Save as PDF" from the
browser gives a PDF; the md export is plain Markdown. Both carry a header:
person label, export time UTC, tools used, entry count, and a footer
"Deleted from the C2O server on <expires_at>".

## 4. Worksheets (from the course workbooks)

Generated, never hand-copied: a script parses the workbook Markdown (EN and
its FR twin) into YAML so the in-tool worksheet text cannot drift from the
printed workbook. A content test asserts the YAML is current (same pattern
as `test_generated_command_reference.py`).

```yaml
# configs/eosat1/worksheets/ops_week3.yaml   (ops; generated)
source: design/docs/course/orbit_north_week3_workbook.md
source_fr: design/docs/course/fr/orbit_north_week3_workbook.md
worksheets:
  - id: WB-5.5-DB
    title: {en: "Day 3 Post-Shift Debrief Reflection", fr: "…"}
    phase: debrief            # prep | during | debrief | exercise
    applies:                  # where the tool offers it (hand-maintained map,
      tools: [mcs, instructor, delayed_tm]   # in worksheet_map.yaml, merged in)
      procedures: []
      pages: []
    questions:
      - {id: q1, text: {en: "…", fr: "…"}, kind: text}   # text | check | number
```

Context matching: procedure ids (e.g. `NOM-001` → WB-5.4-N001,
`LEOP-001` → WB-5.5-L001, `COM-002` → WB-5.6-C002), MCS pages, pre-pass
briefing and debrief phases, delayed-TM anomaly ticket (WB-5.5-AT), etc.
SpaceCDF worksheets come from `design/docs/course/learner_workbook_expanded.md`
(+ `fr/`) into `design/configs/worksheets/learner_workbook.yaml`, matched to
design steps/gates.

## 5. UI (follow docs/ui/C2O_UI_BRIEF.md and the shared tokens)

A **Logbook** button in every tool header (book glyph + count badge), opening
a docked, non-modal side panel (like the MCS alarm drawer):
- Quick-entry box at the top with kind chips (Decision · Thought ·
  Observation · Reflection), Ctrl/Cmd+Enter to save. Context is captured
  automatically (current page, open procedure, selected alarm, study/step,
  sim time) and shown as removable chips before saving.
- **Worksheets** tab: the worksheets that apply to the current context, each
  question answerable inline; answers are `kind: worksheet` entries.
- Entry list (newest first), edit/delete own entries.
- Footer: "Private to you · deleted from the server on <date time> (48 h after
  your last entry)" + **Download** (Markdown / printable HTML) + **Delete now**
  (armed two-step, armButton).
- Contextual "Log this" affordances where a decision is made: next to
  command send / procedure step confirm / GO-NO-GO answer / alarm ACK in the
  MCS; on a report or anomaly in delayed TM; on accept/reject proposal and
  gate review in SpaceCDF. One click opens the panel with context prefilled.
  Never blocks the action.

**End-of-session prompt** (the download prompt):
- An **End session** button in the panel footer opens a dialog: entry count,
  the debrief worksheet for this tool if unanswered, Download buttons, and
  the deletion time.
- Triggered automatically when: a scenario ends (instructor debrief appears;
  the MCS shows it when sim status goes from running to stopped), SpaceCDF
  passes a gate or the user leaves the study, and on `beforeunload` when there
  are entries written since the last download (browser's generic confirm).
- A slim banner when the logbook has entries not downloaded and expires in
  < 12 h.

Storage in the browser: none for the text (server holds it for 48 h). A
draft in the quick-entry box may be kept in sessionStorage in try/catch.

## 6. Instructor prep/debrief

The instructor app's scenario **briefing** pane lists the prep worksheets
for the selected scenario (e.g. WB-5.5-PB before LEOP), and the **debrief**
pane lists the debrief worksheet questions (WB-5.5-DB, WB-5.5-GO) to use in
the spoken debrief, plus a note "participants answer these in their
logbook and download it". The instructor can write their own logbook
entries (same private store) but cannot read participants'. Optional count
view: number of entries per position since scenario start (no text) —
only if positions are known; otherwise omit.

## 7. Ops/deploy

- `compose.yaml`: `SMO_LOGBOOK_DIR=/opt/smo/workspace/logbook` on every
  ground service that mounts the logbook, and mount `ground-workspace` into
  `spacecdf` at `/opt/smo/workspace` (logbook only).
- `deploy/gcp/c2o data` lists logbooks in sizes and can clean them;
  README documents retention and privacy.
- Never commit any logbook data; add `workspace/logbook/` to `.gitignore`.

## 8. Ops workbook (2026-11-02, additive)

Franz: "I want the teams to really use them as work books … make the
checklists part of the log books." The logbook panel's second tab is the
**Workbook** (`smo_common/ui/workbook.js`): the live checklist of the
procedure open or running in the MCS, the forms (anomaly ticket, handover,
GO/NO-GO scorecard, pre-pass briefing, debrief) and an index of every
sheet. Entries stay private per person; nothing is shared on the server.

**Checklists follow the card.** `GET /api/logbook/checklist?procedure=&lang=`
(MCS only; `smo_common/logbook/checklist.py`) builds the checklist from the
procedure CARD, because the card is what is executed; the printed
confirm-each-step row is shown beside each step and every disagreement
between the two is listed (`mismatches`). `python3 -m
smo_common.logbook.checklist configs/eosat1` prints the full report.

**Record additions** (all optional; a reader that ignores them still shows
the record's `text`, which always carries a readable summary):

| Field | Where | Shape |
|---|---|---|
| `worksheet.instance` | worksheet entries | string ≤ 64: the checklist run (`"1"`, `"2"`…) or the form copy (`"AT-0820-42"`, a position) |
| `check` | worksheet entry = one checklist step | `{procedure, step, key, order (int), title, run, result: pass\|fail\|skip\|go\|nogo\|done\|open, source: operator\|runner, position, sim_ts, note, gonogo, runner_run, values: [{param, pid, expect, value, units, ok (bool), stale (bool)}]}` |
| `form` | worksheet entry = one filled form (`worksheet.q = "form"`) | `{instance, fields: [{q, value, checked (bool), prefilled (bool)}], info: [{label, value}]}` |

An `edit` record may carry `check` (merged into the entry's `check`) and
`form` (replaces it). Deviations are `fail`, `skip` and `nogo`.

**Export additions**: `GET /api/logbook/export` also takes `team`,
`position`, `scenario`, `session` (hand-in header), `sheet=<worksheet id>`
(one sheet; file name `c2o-logbook-<sheet>-…`) and `copy=1` (clipboard:
`inline`, no download marker). The document is ordered **Workbook** (sheets
in printed workbook order; checklists as tables — step, check, observed,
time UTC · sim, by, result, note; forms as field/entry tables) then **Log**
(the other entries, chronological). `GET /api/logbook/worksheets?all=1`
lists every sheet of the tool in workbook order (`match` set where it
applies here). Generated sheets carry `form`, `instances`, and per question
`step` (a confirm-each-step row) and `prefill` (a console key).

## 9. Ops UI fixes (2026-11-03)

**One right dock.** The MCS alarm journal, the logbook and the voice loops
stand side by side in `#c2o-dock` (`smo_common/ui/dock.js`) instead of each
overlaying the right edge: open panels narrow the work area (which keeps
≥ 480 px and stacks its page columns by container query); when one more
panel would not fit, the one opened longest ago closes (voice only hides).
Below 1000 px one full-height panel at a time. Tools without a dock keep
the logbook as an overlay.

**Tools without a dock** (delayed TM, radio, orbit tools): on a wide screen
the logbook overlay starts below the page header (language, theme and the
Logbook button stay usable) and follows it on scroll; on a phone it is full
height and never wider than the viewport minus its scrollbar. Only the MCS
serves live checklists: elsewhere a confirm-each-step sheet opens as the
printed sheet, row by row (it used to request the MCS-only checklist route,
get a 404 and show nothing).

**Activity-type cards tick their checklist.** NOM-002/003/004/009 run a
planner activity's command sequence, not the card's TC lines.
`configs/eosat1/mcs/runner_step_map.yaml` maps each runner step to its card
step (checked by a test against the activity types, the runner's loaded
steps and the cards); its EN/FR `notes` ride with the runner's tick where
the activity does the step differently from the card.

**Hand-worked cards are not an error.** `POST /api/procedure/load` for a
card the console cannot run answers 200 `{runnable: false, manual: true,
procedure_id, reason}` (was 409); runnable loads carry `runnable: true`.

**Where the hand-in context comes from** (honest sources only):

| Field | Source | Why this one |
|---|---|---|
| Last completed pass (handover `last_pass`), pass in progress (handover info) | The MCS pass log (`smo_mcs/pass_log.py`, `pass_log` in the MCS state): AOS/LOS from the MCS's own ground propagator (the contact-schedule geometry), first/last TM frame received inside the pass, max elevation. A pass already in progress at console start has no AOS of its own; a backwards time jump forgets passes that now lie in the future. | Ground knowledge a real control centre has; nothing is asked of the simulator. |
| Scenario (export header), Session (handover/briefing/debrief info) | `session_label`, typed by the instructor in the instructor console ("Session label for the consoles") and sent as the `set_session_label` instructor command; the simulator publishes it in `/api/state`, which reaches the ground in the link's STATE feed. The MCS reads only that field, in sim mode only. Empty until the instructor publishes one. | The scenario's own name would brief the operators on the failure (e.g. "Reaction Wheel Stuck at Speed"), and instructor state must not cross the link. A label the instructor chooses to publish, on an existing allowed channel, carries neither. |


## 10. The procedure card is the working copy (2026-11-03)

Franz: "The procedure cards should help the user to go to the workbook to
mark steps as done or not, capture values, and capture decisions (the
procedure cards become part of the logbook as they get filled in)."

`smo_common/ui/procard.js` works on the card as the tool already renders
it. The MCS procedure page (full width, under Load & run) and the
documentation viewer's procedure pages mount it:

- every `### Step N` ends with its controls: **Done / Failed / Skip**
  (**GO / NO-GO / Skip** on a GO/NO-GO gate), the expected value of each
  `**Verify:**` line beside its live value and the value captured,
  **Capture values** (records the live values now, on an open step too; a
  later result keeps them), a note/deviation field (Enter saves) and
  **Record decision** (a logbook `decision` entry prefilled with the
  procedure, step, run and the captured values; context `run` is new);
- every `[ ]` item of `## Prerequisites` / `## Prérequis` is a checkbox;
- a sticky bar: run, progress, deviations, New run, Open in the Workbook.

**One source of truth.** The card calls the Workbook's own `tick()` /
`capture()` (workbook.js): the records are the §8 `check` records, so a
tick in either place shows in both, and the MCS runner's automatic ticks
show on the card. The card keys its headings with `checklist.js`
`cardStepKeys()`, which mirrors `parse_card()` (a test runs every card, EN
and FR). Prerequisites: `checklist.py` `parse_prereqs()` → checklist
`prereqs: [{key: "p1", n: "P1", text, checks?}]`; a prerequisite tick is a
check record with `part: "pre"`, `step: "P1"`. The documentation viewer has
no live TM: no capture there, the tick records the expectation only.

**Export.** The run table is the filled card: prerequisites first, then the
steps; decisions recorded from the card (`context.procedure` + `context.run`)
are printed under the run ("Decisions recorded on this card") instead of in
the log.

## 11. Where to find this (2026-11-04)

Franz: "work through the worksheets with the screens … then add the
additional info where needed." Audit and decisions:
[WORKSHEET_SCREEN_AUDIT_OPS.md](WORKSHEET_SCREEN_AUDIT_OPS.md).

- **Map.** `configs/eosat1/worksheets/worksheet_where.yaml` (hand-maintained)
  gives, per question, its `status` (screen / manual / none / na) and the
  places that answer it: named `targets` (MCS page + panel id / PUS tab /
  drawer tab / parameter row; planner, orbit tools, radio, delayed-TM element
  ids; manual file + heading anchor; procedure card) and open-reference
  `links` (https only, listed in [EXTERNAL_LINKS.md](EXTERNAL_LINKS.md)). A
  question naming a parameter of the operator dictionary gets that row
  without an entry. `tools/gen_worksheets.py` copies the places onto the
  questions as `where: [{tool, page?, param?, focus?, tab?, bd?, path?,
  anchor?, url?, label {en, fr}}]` and writes the audit table (`--audit`;
  `--check` fails when either is stale).
- **Serving.** `smo_common/logbook/worksheets.py localise_where` localises the
  label, keeps only the keys a tool understands, and drops any open
  reference that is not a plain https URL (French URL first, English as the
  fallback). The live checklist carries the printed row's `where` on each
  step (`ref[].where`).
- **Rendering.** `smo_common/ui/where.js` (Workbook tab, forms and checklist
  steps): "Where to find this:" + links. MCS places become
  `#page=…&param=…&focus=…&tab=…&bd=…`, applied in place inside the MCS
  (`mcs.js applyNavHash`: opens the page, marks the row or panel for 15 s) and
  opened in the MCS window (`target="c2o-mcs"`) from any other tool; tool
  addresses follow `tools/portal.py` (cloud `https://<key>.<domain>/`, local
  `http://<host>:<port>/`). Open references: `target="_blank"
  rel="noopener noreferrer"`, marked ↗.
- **Tests.** `tests/test_content/test_worksheet_where.py` (every place exists,
  every parameter row is on its page, the audit is complete and current,
  links https and listed), `tests/test_common/test_where_links.py`
  (where.js under node, doc_viewer link schemes, MCS deep-link validation).
