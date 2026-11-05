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
| Narration voice | Kokoro-82M (Apache-2.0 weights) via kokoro-onnx (MIT); espeak-ng phonemiser for French |
| H5P runtime | H5P content types from the official H5P hub (MIT); h5p-standalone player (MIT) |

The pipeline does not use XTTS-v2 (its licence is non-commercial, outputs
included), edge-tts (Microsoft's service terms) or Remotion (it needs a
company licence for universities).

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

On GCP, `deploy/gcp/c2o videos push` copies the published folder to the ground VM.

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
