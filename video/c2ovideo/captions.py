"""WebVTT captions and chapters from the narration script and the cue log.

No speech recognition is involved: each sentence was synthesised on its own,
so its start and length are known exactly.
"""

from __future__ import annotations

from dataclasses import dataclass

MAX_LINE = 42
MAX_CUE = 2 * MAX_LINE


@dataclass
class Placed:
    step: str
    text: str           # written form
    start: float        # seconds from the start of the video
    seconds: float
    path: object        # wav path


def ts(t: float) -> str:
    t = max(0.0, t)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def _chunks(text: str) -> list[str]:
    words = text.split()
    out, cur = [], ""
    for w in words:
        if len(cur) + 1 + len(w) > MAX_CUE and cur:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        out.append(cur)
    # avoid a dangling one- or two-word last cue
    if len(out) > 1 and len(out[-1].split()) <= 2 and len(out[-2]) + len(out[-1]) < MAX_CUE + 12:
        last = out.pop()
        out[-1] = out[-1] + " " + last
    return out


def _two_lines(text: str) -> str:
    if len(text) <= MAX_LINE:
        return text
    mid = len(text) // 2
    spaces = [i for i, ch in enumerate(text) if ch == " "]
    if not spaces:
        return text
    cut = min(spaces, key=lambda i: abs(i - mid))
    return text[:cut] + "\n" + text[cut + 1:]


def vtt(placed: list[Placed], lang: str) -> str:
    lines = ["WEBVTT", f"Language: {lang}", ""]
    n = 0
    for p in placed:
        parts = _chunks(p.text)
        total = sum(len(x) for x in parts) or 1
        t = p.start
        for part in parts:
            d = p.seconds * len(part) / total
            n += 1
            lines += [str(n), f"{ts(t)} --> {ts(t + d)}", _two_lines(part), ""]
            t += d
    return "\n".join(lines)


def chapters(items: list[tuple[float, float, str]]) -> str:
    lines = ["WEBVTT", ""]
    for i, (a, b, title) in enumerate(items, 1):
        lines += [f"ch{i}", f"{ts(a)} --> {ts(b)}", title, ""]
    return "\n".join(lines)


def transcript(sb_title: str, steps: list[tuple[str, str]]) -> str:
    out = [f"# {sb_title}", ""]
    for title, text in steps:
        out += [f"## {title}", "", text, ""]
    return "\n".join(out)
