"""Compare English narration settings for the cloned voice, so the accent can be chosen by ear.

    python3 video/scripts/voice_ab.py                       # four variants, three sentences
    python3 video/scripts/voice_ab.py --ref ~/Downloads/other_take.wav   # also try another reference

Writes one WAV per variant (the three sentences joined) to video/out/voice_ab/ and prints
the list. Pick the best one and copy its settings into voices.yaml (en:). Nothing is cached,
so the main narration cache is untouched.

Variants:
  A  multilingual model, exaggeration 0.5, cfg 0.5   (what the videos use now)
  B  English-only model,  exaggeration 0.5, cfg 0.5
  C  English-only model,  exaggeration 0.35, cfg 0.6 (calmer, follows the reference more closely)
  D  multilingual model,  exaggeration 0.35, cfg 0.6
  R* the same as B and C with the alternative reference recording, if --ref is given
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from c2ovideo import tts  # noqa: E402

SENTENCES = [
    "The operator then commands fine pointing, and the attitude error falls below one tenth of a degree.",
    "Before the pass, the team checks the battery state of charge and the temperature of the payload.",
    "Lake ice and open water look very different at short-wave infrared wavelengths, which is why the second camera matters.",
]


def render(engine: dict, out: Path) -> None:
    parts = []
    for s in SENTENCES:
        a = tts._synth(dict(engine), s, "en")
        parts += [a, np.zeros(int(0.5 * tts.SR), dtype=a.dtype)]
    tts.write_wav(out, np.concatenate(parts))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", type=Path, help="alternative English reference recording (10-15 s)")
    ap.add_argument("--out", type=Path, default=HERE / "out" / "voice_ab")
    a = ap.parse_args()
    base = tts.engine_for("en", None)
    if base.get("backend") != "chatterbox":
        raise SystemExit("voices.yaml en: is not a chatterbox voice")
    variants = {
        "A_multilingual_0.5_0.5": dict(base, model="multilingual", exaggeration=0.5, cfg_weight=0.5),
        "B_english_0.5_0.5": dict(base, model="english", exaggeration=0.5, cfg_weight=0.5),
        "C_english_0.35_0.6": dict(base, model="english", exaggeration=0.35, cfg_weight=0.6),
        "D_multilingual_0.35_0.6": dict(base, model="multilingual", exaggeration=0.35, cfg_weight=0.6),
    }
    if a.ref:
        ref = str(a.ref.expanduser().resolve())
        variants["RB_altref_english_0.5_0.5"] = dict(variants["B_english_0.5_0.5"], ref=ref)
        variants["RC_altref_english_0.35_0.6"] = dict(variants["C_english_0.35_0.6"], ref=ref)
    a.out.mkdir(parents=True, exist_ok=True)
    for name, eng in variants.items():
        p = a.out / f"{name}.wav"
        print(f"rendering {name} ...", flush=True)
        render(eng, p)
        print(f"  {p}")
    print("\nListen, pick one, then set in video/voices.yaml under en:")
    print("  model: english | multilingual, exaggeration: ..., cfg_weight: ...")


if __name__ == "__main__":
    main()
