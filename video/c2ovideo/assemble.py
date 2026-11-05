"""Frames + narration + cards → MP4, captions, chapters, poster, transcript."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

from . import captions, cards, tts, worksheets
from .storyboard import Storyboard, tr

FPS = 30
TITLE_S = 3.2
END_S = 4.5


def _ffconcat(entries: list[tuple[Path, float]], path: Path) -> None:
    lines = ["ffconcat version 1.0"]
    for f, d in entries:
        lines += [f"file '{f.as_posix()}'", f"duration {d:.4f}"]
    lines.append(f"file '{entries[-1][0].as_posix()}'")       # concat demuxer quirk: repeat last
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build(sb: Storyboard, lang: str, take: Path, clips: dict[str, list[tts.Clip]], out: Path) -> dict:
    """``take`` holds frames/ and cues.json from ``capture``; writes into ``out``."""
    cues = json.loads((take / "cues.json").read_text(encoding="utf-8"))
    out.mkdir(parents=True, exist_ok=True)
    stem = f"{sb.slug}.{lang}"
    end_t = cues["cues"][-1]["end"] + 0.5
    off = TITLE_S                                     # everything shifts by the title card

    # -- video: title card, timestamped frames from t=0, end card
    frames = cues["frames"]
    first = 0
    for i, (t, _) in enumerate(frames):
        if t <= 0:
            first = i
    seq = [(t, n) for t, n in frames[first:] if t < end_t]
    if not seq:
        raise RuntimeError(f"{sb.id} [{lang}]: the capture has no frames")
    title, endcard = cards.render(sb, lang, take, worksheets.end_card_ties(sb, lang))
    entries = [(title, TITLE_S)]
    # resample onto the output frame grid: frame shown at tick k is the last one captured
    # at or before k/FPS (bursts faster than FPS are dropped, so timing stays exact)
    seq.sort(key=lambda x: x[0])
    ticks = int(end_t * FPS)
    j, cur, run = 0, seq[0][1], 0
    for k in range(ticks):
        tk = k / FPS
        while j + 1 < len(seq) and seq[j + 1][0] <= tk:
            j += 1
        name = seq[j][1]
        if name != cur and run:
            entries.append((take / "frames" / cur, run / FPS))
            run = 0
        cur = name
        run += 1
    if run:
        entries.append((take / "frames" / cur, run / FPS))
    entries.append((endcard, END_S))
    total = TITLE_S + end_t + END_S
    concat = take / "frames.ffconcat"
    _ffconcat(entries, concat)

    # -- audio: each sentence at its exact place
    audio = np.zeros(int(total * tts.SR) + tts.SR, dtype=np.float32)
    placed: list[captions.Placed] = []
    cue_by_id = {c["id"]: c for c in cues["cues"]}
    late = []
    for st in sb.steps:
        room = cue_by_id[st.id]["end"] - cue_by_id[st.id]["say"]
        if tts.total_seconds(clips.get(st.id, [])) > room + 0.05:
            late.append(f"narration of step {st.id} runs past its take ({room:.1f} s): re-capture")
        t = cue_by_id[st.id]["say"] + off
        for c in clips.get(st.id, []):
            a = tts.read_wav(c.path)
            i = int(t * tts.SR)
            audio[i:i + len(a)] += a[: max(0, len(audio) - i)]
            placed.append(captions.Placed(step=st.id, text=c.text, start=t, seconds=c.seconds, path=c.path))
            t += c.seconds + tts.GAP_S
    wav = take / "narration.wav"
    tts.write_wav(wav, audio[: int(total * tts.SR)])

    mp4 = out / f"{stem}.mp4"
    w, h = sb.size
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(concat), "-i", str(wav),
           "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,fps={FPS},format=yuv420p",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-g", str(FPS * 4),
           "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-t", f"{total:.3f}",
           "-metadata", f"title={tr(sb.title, lang)}", "-metadata", "copyright=CC0 1.0",
           "-metadata", f"language={'fra' if lang == 'fr' else 'eng'}", "-movflags", "+faststart", str(mp4)]
    subprocess.run(cmd, check=True)

    # -- captions, chapters, transcript, poster
    (out / f"{stem}.vtt").write_text(captions.vtt(placed, lang), encoding="utf-8")
    chap = []
    starts = [(cue_by_id[s.id]["start"] + off, s) for s in sb.steps if s.chapter]
    for i, (a, s) in enumerate(starts):
        b = starts[i + 1][0] if i + 1 < len(starts) else off + end_t
        chap.append((a, b, tr(s.title, lang)))
    (out / f"{stem}.chapters.vtt").write_text(captions.chapters(chap), encoding="utf-8")
    (out / f"{stem}.transcript.md").write_text(
        captions.transcript(tr(sb.title, lang), [(tr(s.title, lang), tr(s.say, lang)) for s in sb.steps]), encoding="utf-8")
    mid = seq[min(len(seq) - 1, int(len(seq) * 0.45))][1]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(take / "frames" / mid), "-vf", f"scale={min(w, 1280)}:-2",
                    "-q:v", "3", str(out / f"{stem}.poster.jpg")], check=True)
    questions = []
    for st in sb.steps:
        if st.question:
            questions.append({"step": st.id, "time": round(cue_by_id[st.id]["end"] + off - 0.15, 2)})
    meta = {"id": sb.id, "lang": lang, "duration": round(total, 2), "offset": off,
            "chapters": [{"start": round(a, 2), "title": t} for a, _, t in chap], "questions": questions,
            "warnings": late + cues.get("warnings", [])}
    (out / f"{stem}.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    return meta
