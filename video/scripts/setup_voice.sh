#!/usr/bin/env bash
# One-time set-up for rendering the course videos with the cloned narration voice.
# Tested target: macOS on Apple silicon (the voice model uses the GPU through MPS).
#
#   bash video/scripts/setup_voice.sh /path/to/franz_en.wav /path/to/franz_fr.wav
#
# The two reference recordings are personal: they are copied into
# ~/.cache/c2o-video/voices/ and never into the repository.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"          # .../video
repo="$(cd "$here/.." && pwd)"
voices="${C2O_VIDEO_CACHE:-$HOME/.cache/c2o-video}/voices"
venv="$HOME/cbx-venv"

say() { printf '\n== %s\n' "$*"; }

# 1. Voice references -------------------------------------------------------
if [ $# -ge 2 ]; then
  mkdir -p "$voices"
  cp "$1" "$voices/franz_en.wav"
  cp "$2" "$voices/franz_fr.wav"
fi
for f in franz_en.wav franz_fr.wav; do
  [ -f "$voices/$f" ] || { echo "Missing $voices/$f. Pass the two reference .wav files as arguments."; exit 1; }
done
say "voice references in $voices"

# 2. Chatterbox in its own environment (it pins torch 2.6 and transformers 5.2) --
py=""
for c in python3.11 python3.12 python3.10; do command -v "$c" >/dev/null && { py="$c"; break; }; done
[ -n "$py" ] || { echo "Needs Python 3.10-3.12 (brew install python@3.11)."; exit 1; }
if [ ! -x "$venv/bin/python" ]; then
  say "creating $venv with $py"
  "$py" -m venv "$venv"
fi
"$venv/bin/python" -m pip install -q --upgrade pip
say "installing Chatterbox (a few GB the first time)"
# setuptools < 81: the Perth watermarker still imports pkg_resources, which 81 removed;
# without it Chatterbox fails at start-up with "'NoneType' object is not callable".
"$venv/bin/python" -m pip install -q "chatterbox-tts==0.1.7" "setuptools<81"

# 3. The video pipeline itself -----------------------------------------------
say "video pipeline requirements"
python3 -m pip install -q -r "$here/requirements.txt"
python3 -m playwright install chromium
command -v ffmpeg >/dev/null || { echo "ffmpeg is missing: brew install ffmpeg"; exit 1; }
cd "$here"
python3 -m c2ovideo fetch-h5p
[ -x "$repo/sim/.venv/bin/python" ]    || python3 -m c2ovideo stack setup sim
[ -x "$repo/design/.venv/bin/python" ] || python3 -m c2ovideo stack setup spacecdf
if [ ! -d "$repo/design/frontend/dist" ]; then
  say "building the SpaceCDF front end"
  (cd "$repo/design/frontend" && npm ci && npm run build)
fi

# 4. Smoke test: one sentence in each language --------------------------------
say "test sentence (the first run downloads the voice model, about 3 GB)"
"$venv/bin/python" -c "import chatterbox.mtl_tts, torch; print('chatterbox', 'MPS' if torch.backends.mps.is_available() else 'CPU')" \
  || { echo "Chatterbox does not import in $venv: see the error above."; exit 1; }
if python3 -m c2ovideo narrate V-OPS-13 --lang en >/dev/null && python3 -m c2ovideo narrate V-OPS-13 --lang fr >/dev/null; then
  say "ready: bash video/scripts/render_all.sh"
else
  echo "The voice test failed. Worker log: ${C2O_VIDEO_CACHE:-$HOME/.cache/c2o-video}/cbx_worker.log"
  exit 1
fi
