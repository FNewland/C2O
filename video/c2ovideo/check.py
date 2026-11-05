"""Listen back: speech recognition on every narration sentence.

Each synthesised sentence is transcribed (faster-whisper, MIT, run locally)
and compared with the script. A low score means the voice probably said
something a student would not understand: a mispronounced identifier, a
French word read in English, a dropped number. The report lists the worst
sentences first so a reviewer listens to those before anything else.

Optional: ``pip install faster-whisper`` (the model downloads on first use).
"""

from __future__ import annotations

import difflib
import json
import re
import unicodedata

import numpy as np

from . import tts
from .__main__ import OUT, narrate
from .storyboard import Storyboard


def _norm(s: str) -> list[str]:
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return s.split()


def score(expected: str, heard: str) -> float:
    a, b = _norm(expected), _norm(heard)
    if not a:
        return 1.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def run(sb: Storyboard, langs: list[str], model: str = "small") -> int:
    from faster_whisper import WhisperModel
    m = WhisperModel(model, device="cpu", compute_type="int8")
    report = {}
    worst = []
    for lang in langs:
        rows = []
        for step, clips in narrate(sb, lang).items():
            for c in clips:
                a = tts.read_wav(c.path)
                a16 = np.interp(np.linspace(0, len(a), int(len(a) * 16000 / tts.SR), endpoint=False), np.arange(len(a)), a).astype(np.float32)
                segs, _ = m.transcribe(a16, language=lang, beam_size=1, vad_filter=False)
                heard = " ".join(s.text.strip() for s in segs)
                sc = score(c.spoken, heard)
                rows.append({"step": step, "text": c.text, "spoken": c.spoken, "heard": heard, "score": round(sc, 3)})
                worst.append((sc, lang, step, c.text, heard))
        report[lang] = rows
        mean = sum(r["score"] for r in rows) / max(1, len(rows))
        print(f"[{lang}] {len(rows)} sentences, mean match {mean:.2f}")
    out = OUT / sb.slug / "narration_check.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    worst.sort()
    print("lowest matches (listen to these first):")
    for sc, lang, step, text, heard in worst[:8]:
        print(f"  {sc:.2f} [{lang}] {step}: {text}\n         heard: {heard}")
    print("report:", out)
    return 0
