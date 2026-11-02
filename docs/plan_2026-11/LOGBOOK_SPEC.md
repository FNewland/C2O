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
