"""Narration review data: EN and FR side by side, sentence audio, risky tokens.

The welcome page shows it to instructors at /videos/<id>/review, plays every
sentence, and saves a note per step and language. ``python -m c2ovideo
reviews`` prints the open notes so the storyboard can be fixed and re-rendered.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from . import LANGS, lexicon, tts
from .storyboard import Storyboard, tr


def build(sb: Storyboard, clips: dict[str, dict[str, list[tts.Clip]]], out: Path) -> Path:
    """``clips[lang][step_id]``; writes ``out/review/`` (review.json + mp3 per sentence)."""
    rd = out / "review"
    if rd.exists():
        shutil.rmtree(rd)
    rd.mkdir(parents=True)
    steps = []
    for st in sb.steps:
        row = {"id": st.id}
        for lang in LANGS:
            sent = []
            for i, c in enumerate(clips.get(lang, {}).get(st.id, [])):
                name = f"{st.id}.{lang}.{i}.mp3"
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(c.path), "-b:a", "64k", str(rd / name)], check=True)
                sent.append({"text": c.text, "spoken": c.spoken, "audio": name, "seconds": round(c.seconds, 2)})
            row[lang] = {"title": tr(st.title, lang), "say": tr(st.say, lang), "sentences": sent,
                         "unknown": lexicon.unknown_tokens(tr(st.say, lang), lang)}
            if st.question:
                q = st.question
                row[lang]["question"] = {"type": q["type"], "text": tr(q["text"], lang),
                                         "options": [tr(o["text"], lang) for o in q.get("options", [])]}
        steps.append(row)
    data = {"id": sb.id, "title": {l: tr(sb.title, l) for l in LANGS}, "steps": steps,
            "voices": {l: {k: v for k, v in tts.engine_for(l).items()} for l in LANGS}}
    (rd / "review.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    return rd
