# C2O course videos

Short walkthrough videos of the C2O tools, in English and European French,
with questions that pause the video and feed the course workbook. Every video is
**generated**: a storyboard drives the real tool in a browser, a local voice
model reads the narration, and the pipeline writes the MP4, the captions and
an H5P Interactive Video for Brightspace. Change a storyboard or the UI and
re-render. Nothing is edited by hand.

| | |
|---|---|
| Code (`c2ovideo/`) | MIT (`LICENSE`) |
| Storyboards, lexicons, rendered videos, captions, transcripts, H5P content | CC0 1.0 (public domain) |
| Narration voice | Franz Newland's voice, cloned with Chatterbox Multilingual (Resemble AI, MIT; output carries the inaudible Perth watermark). Kokoro-82M (Apache-2.0) remains available as a fallback in `voices.yaml` |
| H5P runtime | H5P content types from the official H5P hub (MIT); h5p-standalone player (MIT) |

The pipeline does not use XTTS-v2 (its licence is non-commercial, outputs
included), edge-tts (Microsoft's service terms) or Remotion (it needs a
company licence for universities).

## Rendering with the cloned voice

The narration uses Chatterbox Multilingual, which reproduces a speaker from a
15-second reference recording in each language. The references are personal and
are **not** in this repository: they live in `~/.cache/c2o-video/voices/`
(`franz_en.wav`, `franz_fr.wav`; 24 kHz mono, normalised to -20 LUFS).
`voices.yaml` points at them and at the separate Python environment
(`~/cbx-venv`) that Chatterbox needs.

On a Mac with Apple silicon:

```bash
bash video/scripts/setup_voice.sh ~/Downloads/franz_en.wav ~/Downloads/franz_fr.wav   # once
bash video/scripts/render_all.sh            # all videos, EN and FR; resumable
bash video/scripts/render_all.sh V-OPS-02   # or named videos only
bash video/scripts/render_all.sh sim        # simulator videos (V-OPS, V-PLN); also: scdf, design, concepts
bash video/scripts/render_all.sh list       # groups, video IDs and which are done
LANG_ONLY=en FORCE=1 bash video/scripts/render_all.sh sim design concepts   # redo English only, skip SpaceCDF
```

The voice runs on the GPU (MPS) when available, otherwise on the CPU; set
`C2O_CBX_DEVICE=cpu` to force one. On a 2-core cloud CPU it produces about one
sentence a minute; an M-series Mac is several times faster. Each sentence is
cached under `~/.cache/c2o-video/tts/`, keyed by the text and the reference
recording, so re-running after a script change only re-voices the sentences that
changed. Pronunciation fixes for identifiers (FINE_POINT, HIGH, DETUMBLE, ...)
go in `lexicon/en.yaml` and `lexicon/fr.yaml`.

## One storyboard, two languages

`storyboards/V-SCDF-01.yaml` is the reference. Each step has:

* `title` and `say` in `{en, fr}`: the chapter title and the narration;
* `do`: what the browser does. Selectors are language-neutral (CSS, `data-*`)
  or name the English UI string (`{role: button, name: Create New Mission}`).
  The runner finds the French string in the tool's own catalogue, so the
  storyboard never repeats a translation;
* an optional `question` (multichoice, truefalse, blanks, reflect). The video
  pauses on it at the end of the step. `worksheet: LW-1.4/B` ties it to the
  workbook part it prepares.

Top-level `ties` (worksheets, decisions, procedure cards) appear on the closing
card ("Now, in your workbook"), in the library, and beside the player. The
graded gate quiz (WB-5.4-Q) can never be tied to a video.

Typed content can differ by language (`text: {en: …, fr: …}`).

## Run it

```bash
cd video
pip install -r requirements.txt            # once; Playwright's Chromium too (python -m playwright install chromium)
python -m c2ovideo fetch-models            # Kokoro voice model, ~120 MB, once
python -m c2ovideo fetch-h5p               # H5P runtime libraries, ~4 MB, once
python -m c2ovideo stack setup sim         # sim/.venv with the simulator (needs Python 3.11+), once
python -m c2ovideo stack setup spacecdf    # design/.venv with SpaceCDF, once
(cd ../design/frontend && npm ci && npm run build)   # the SpaceCDF UI the videos film
python -m c2ovideo validate                # every storyboard: ties, French UI strings

python -m c2ovideo stack up spacecdf       # SpaceCDF on :18800 with a throw-away database
python -m c2ovideo build V-SCDF-01 --publish
python -m c2ovideo stack down spacecdf

python -m c2ovideo stack up sim            # simulator, MCS, planner, tools on the usual ports
python -m c2ovideo build V-OPS-01 --publish
python -m c2ovideo stack down sim
```

`--tts silence` makes a dry run without the voice model. `--reuse-capture`
re-assembles without re-recording. `--lang fr` renders one language only.

`build` writes to `out/<id>/`:

* `<id>.<lang>.mp4`: 1920×1080 H.264, AAC, a title card and a closing workbook card;
* `.vtt`: captions built from the script, with no speech recognition;
* `.chapters.vtt`;
* `.transcript.md`;
* `.poster.jpg`;
* `.h5p`: upload as is to Brightspace (uOttawa's H5P). It carries its own video,
  captions and French UI strings;
* `review/`: every sentence as audio, with the text the voice was given.

`publish` copies everything into `sim/workspace/videos`, which the welcome page serves:

* `/videos`: the library;
* `/videos/<id>`: the interactive player. Answers go into the viewer's logbook,
  against the worksheet they belong to;
* `/videos/<id>/review`: narration review, EN and FR side by side, with a note per
  step. It is for instructors and the accounts in `SMO_VIDEO_REVIEWERS`.

On GCP: `deploy/gcp/c2o update` once (so the server has the `/videos` pages), then
`deploy/gcp/c2o videos push` copies the published folder to the ground VM.

## Acronyms, jargon, explanations, audience

Every script follows these rules (from the 2026-11-06 script review,
`docs/plan_2026-11/script_review/`):

1. **First use, full form.** The first time a video *says* an acronym, it says
   the full form, then the short form the team uses: "nominal procedure one,
   NOM-001", "the attitude and orbit control system, the AOCS" / « le système
   de contrôle d’attitude et d’orbite, le SCAO ». After that, the short form:
   operators work in acronyms, and learners should get used to hearing them.
   Each video stands alone, so this is per video and per language.
2. The register is `lexicon/acronyms.yaml`: expansion in EN and FR, how the
   team says the short form, and `expand: false` for names, mode names and
   on-screen values (GO, SAFE, DETUMBLE, GPS…). Add new acronyms there first.
   How the voice *pronounces* them stays in `lexicon/en.yaml` / `fr.yaml`.
3. `python -m c2ovideo validate` warns (`! acronym:`) when a first use has no
   expansion nearby. It never blocks a build.
4. Opaque jargon that is not an acronym (B-dot, light time, orbit-average
   margin) gets a short plain gloss at first use too.
5. Each storyboard has an `audience:` — `all` when the whole team needs it to
   follow the pass or the poll, or a list of console positions
   (`flight_director`, `eps_tcs`, `aocs`, `ttc`, `payload_ops`,
   `fdir_systems`, `propulsion`) when only those seats command or judge it.
   No videos for instructors.
6. When a step needs more depth than the card gives, do not lengthen the
   walkthrough: point to (or make) a short concept explainer built from the
   textbook (`design/docs/oer/chapters/`), animated by replaying a
   `shared/ui-viz` module or with Manim / Motion Canvas.

## Rebuild everything that changed

```bash
source .venv/bin/activate                  # the video environment, not conda (base)
python -m c2ovideo build-all --dry-run     # what would be built, and why
python -m c2ovideo build-all --publish     # build them, one after another
python -m c2ovideo build-all V-OPS-05      # just these (a held video named here is built)
```

Each build records a fingerprint of its inputs in `out/<id>/build.json`: the storyboard,
the lexicons and voices, the pipeline code, and the sources of every tool it films (for an
ops video the simulator, MCS, configs, cards and worksheets; for SpaceCDF the frontend and
server; for an explainer its page and data). `build-all` skips a video whose fingerprint is
unchanged. A storyboard with `hold: "reason"` is skipped and listed with its reason. Failed
videos are listed at the end and do not stop the run; captured frames are deleted after each
video (`--keep-frames` to keep them), since they take 0.5–1 GB per language.

## Concept explainers

`explainers/` holds the animated concept pages: one self-contained, bilingual SVG page per
explainer, built on `explainer.js` (a tiny scene engine) and `explainer.css` (the console
look: grey at rest, colour for meaning). Labels sit in an `EX.labels({en, fr})` table;
identifiers stay English. A storyboard opens the page on the `viz` app and drives it:

```yaml
apps: {viz: default}
fresh_stack: viz                 # python -m c2ovideo stack up viz  (static server, :18801)
setup:
  - goto: {app: viz, path: "/video/explainers/tc-life.html?lang={lang}"}
steps:
  - id: accept
    say: {en: ..., fr: ...}
    do:
      - js: "EX.play('accept', ${say})"   # ${say} = this step's narration in seconds
```

A scene schedules its beats as fractions of the narration (`beat(0.5, fn)` fires half-way),
so the picture and the voice stay together in both languages. Data for a page goes in
`explainers/data/`, made by a script from the simulator's own models (see
`gen_energy_orbit.py`), never typed in. The tests check that every scene a storyboard plays
exists and that both label tables have the same keys.

## French review

1. `python -m c2ovideo check <id>` runs speech recognition on every sentence and
   lists the worst matches first. That is where a mispronounced identifier
   shows up.
2. Reviewers open `/videos/<id>/review`, listen, and leave notes.
3. `python -m c2ovideo reviews` prints the open notes.
4. Fix the wording in the storyboard, or the pronunciation in `lexicon/fr.yaml`.
   Then re-render.

Identifiers stay English on screen (the bilingual rule). The lexicon says them
the way an operator reads them aloud.
