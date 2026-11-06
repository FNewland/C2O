"""Lint: the first time a video says an acronym, it says the full form too.

The register is ``video/lexicon/acronyms.yaml``. Each video stands alone
(learners watch them out of order), so the first use is counted per video and
per language, across the steps in order. A first use passes when the leading
words of the expansion appear close to it, before or after ("the attitude and
orbit control system, AOCS" or "AOCS, attitude and orbit control").

Warnings only: they never stop a build.
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

import yaml

from .storyboard import ROOT

WINDOW_BEFORE = 140
WINDOW_AFTER = 180
STOP = {"the", "and", "of", "for", "a", "an", "de", "du", "des", "la", "le", "les", "et", "d", "l", "à", "un", "une"}


@lru_cache(maxsize=None)
def register() -> dict:
    f = ROOT / "lexicon" / "acronyms.yaml"
    return yaml.safe_load(f.read_text(encoding="utf-8")) or {}


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.replace("’", "'")).encode("ascii", "ignore").decode()
    return s.lower()


def _keywords(expansion: str) -> list[str]:
    words = [w for w in re.findall(r"[a-z]+", _fold(expansion)) if w not in STOP and len(w) > 2]
    return words[:3]


def _expanded(text: str, pos: int, end: int, expansion: str) -> bool:
    win = _fold(text[max(0, pos - WINDOW_BEFORE):end + WINDOW_AFTER])
    keys = _keywords(expansion)
    if not keys:
        return True
    need = min(2, len(keys))
    # stems: "magnetorquers" matches "magnetorquer", "commissioning" ~ "commission"
    return sum(1 for k in keys if k[:max(5, len(k) - 2)] in win) >= need


def lint(sb) -> list[str]:
    reg = register()
    out = []
    for lang in ("en", "fr"):
        text = ""
        starts = []
        for st in sb.steps:
            starts.append((len(text), st.id))
            text += (st.say.get(lang) or "") + " \n"
        seen = set()
        for key, info in reg.items():
            if not isinstance(info, dict) or not info.get("expand") or key == "S1":
                continue
            m = re.search(rf"(?<![\w.]){re.escape(key)}(?![\w])", text)
            if not m or key in seen:
                continue
            seen.add(key)
            if not _expanded(text, m.start(), m.end(), info.get(lang) or ""):
                step = [sid for p, sid in starts if p <= m.start()][-1]
                out.append(f"{lang} {step}: first '{key}' is not expanded "
                           f"(say \"{info.get(lang)}\" with it)")
        # PUS services, S1…S20: the first one says "service n"
        m = re.search(r"(?<![\w.])S(\d{1,2})(?![\w])", text)
        if m:
            word = "service"
            win = _fold(text[max(0, m.start() - WINDOW_BEFORE):m.end() + WINDOW_AFTER])
            if word not in win:
                step = [sid for p, sid in starts if p <= m.start()][-1]
                out.append(f"{lang} {step}: first '{m.group(0)}' is not expanded (say \"service {m.group(1)}\")")
    return out
