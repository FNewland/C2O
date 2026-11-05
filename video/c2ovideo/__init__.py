"""C2O course video pipeline.

One language-neutral storyboard (``video/storyboards/*.yaml``) becomes, for each
language (EN, FR):

1. narration audio (offline TTS, one clip per sentence, pronunciation lexicon);
2. a screen capture of the real tool, paced to that narration (Playwright,
   Chrome DevTools screencast, drawn cursor);
3. WebVTT captions and chapters built from the script text and the cue log;
4. an MP4 (ffmpeg);
5. an H5P Interactive Video package with embedded questions tied to the
   course worksheets;
6. a review sheet (EN and FR side by side, with audio) for the French check;

and ``publish`` copies the result into the folder the C2O welcome page serves
(``/videos``).

Code: MIT (``video/LICENSE``). Storyboards, narration and rendered media: CC0 1.0.
See ``video/README.md``.
"""

__version__ = "0.1.0"

LANGS = ("en", "fr")
