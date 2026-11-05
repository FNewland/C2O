"""Storyboard loading and validation.

A storyboard is one YAML file per video. Everything a viewer sees or hears is
given in both languages (``{en: ..., fr: ...}``); everything the browser does is
language-neutral (selectors, data attributes, English UI strings that the
runner translates through the tool's own catalogue). See ``video/README.md``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from . import LANGS

ROOT = Path(__file__).resolve().parents[1]          # video/
REPO = ROOT.parent                                   # repository root
STORYBOARDS = ROOT / "storyboards"

ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]{2,40}$")
STEP_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,40}$")
QUESTION_TYPES = {"multichoice", "truefalse", "blanks", "reflect"}
APPS = {"spacecdf", "mcs", "planner", "instructor", "tools", "docs", "portal", "viz", "file"}


class StoryboardError(ValueError):
    pass


def tr(value: Any, lang: str) -> Any:
    """Pick ``lang`` from an ``{en, fr}`` mapping; pass anything else through."""
    if isinstance(value, dict) and set(value) <= set(LANGS) | {"t"} and value:
        if lang in value:
            return value[lang]
        return value.get("en")
    return value


@dataclass
class Step:
    id: str
    title: dict
    say: dict
    do: list = field(default_factory=list)
    hold: float = 0.6
    say_after: bool = False          # narration starts after the actions finish
    question: dict | None = None
    chapter: bool = True


@dataclass
class Storyboard:
    path: Path
    id: str
    title: dict
    summary: dict
    week: int | None
    apps: dict
    viewport: tuple[int, int]
    scale: float
    setup: list
    steps: list[Step]
    ties: dict
    sources: list
    licence: str
    raw: dict

    @property
    def slug(self) -> str:
        return self.id.lower()

    @property
    def size(self) -> tuple[int, int]:
        """Output frame size in pixels (viewport × device scale), even numbers."""
        w, h = (round(self.viewport[0] * self.scale), round(self.viewport[1] * self.scale))
        return w - w % 2, h - h % 2


def _need_both(obj: Any, where: str) -> None:
    if not isinstance(obj, dict) or not all(isinstance(obj.get(l), str) and obj.get(l).strip() for l in LANGS):
        raise StoryboardError(f"{where}: needs non-empty text for {', '.join(LANGS)}")


def _check_question(q: dict, where: str) -> None:
    kind = q.get("type")
    if kind not in QUESTION_TYPES:
        raise StoryboardError(f"{where}: question type must be one of {sorted(QUESTION_TYPES)}")
    _need_both(q.get("text"), f"{where}.text")
    if kind == "multichoice":
        opts = q.get("options") or []
        if len(opts) < 2 or not any(o.get("correct") for o in opts):
            raise StoryboardError(f"{where}: multichoice needs ≥2 options and one correct")
        for i, o in enumerate(opts):
            _need_both(o.get("text"), f"{where}.options[{i}]")
    elif kind == "truefalse":
        if not isinstance(q.get("answer"), bool):
            raise StoryboardError(f"{where}: truefalse needs answer: true|false")
    elif kind == "blanks":
        for l in LANGS:
            if "*" not in (q.get("text") or {}).get(l, ""):
                raise StoryboardError(f"{where}: blanks text must mark answers as *answer* ({l})")
    if q.get("worksheet") is not None and not isinstance(q.get("worksheet"), str):
        raise StoryboardError(f"{where}: worksheet must be an id string")


def load(path: str | Path) -> Storyboard:
    p = Path(path)
    if not p.exists():
        cand = STORYBOARDS / f"{path}.yaml"
        if cand.exists():
            p = cand
        else:
            hits = [f for f in STORYBOARDS.glob("*.yaml") if f.stem.lower().startswith(str(path).lower())]
            if len(hits) == 1:
                p = hits[0]
            else:
                raise StoryboardError(f"storyboard not found: {path}")
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    sid = raw.get("id", "")
    if not ID_RE.match(sid):
        raise StoryboardError(f"{p.name}: id must look like V-SCDF-01 (got {sid!r})")
    _need_both(raw.get("title"), f"{sid}.title")
    _need_both(raw.get("summary"), f"{sid}.summary")
    apps = raw.get("apps") or {}
    for a in apps:
        if a not in APPS:
            raise StoryboardError(f"{sid}: unknown app {a!r} (known: {sorted(APPS)})")
    vp = raw.get("viewport", [1280, 720])
    steps = []
    seen = set()
    for i, s in enumerate(raw.get("steps") or []):
        where = f"{sid}.steps[{i}]"
        stid = s.get("id", "")
        if not STEP_ID_RE.match(stid) or stid in seen:
            raise StoryboardError(f"{where}: step id missing, malformed or repeated ({stid!r})")
        seen.add(stid)
        _need_both(s.get("title"), f"{where}.title")
        _need_both(s.get("say"), f"{where}.say")
        q = s.get("question")
        if q:
            _check_question(q, f"{where}.question")
        steps.append(Step(id=stid, title=s["title"], say=s["say"], do=list(s.get("do") or []),
                          hold=float(s.get("hold", 0.6)), say_after=bool(s.get("say_after", False)),
                          question=q, chapter=bool(s.get("chapter", True))))
    if not steps:
        raise StoryboardError(f"{sid}: no steps")
    return Storyboard(path=p, id=sid, title=raw["title"], summary=raw["summary"], week=raw.get("week"),
                      apps=apps, viewport=(int(vp[0]), int(vp[1])), scale=float(raw.get("scale", 1.5)), setup=list(raw.get("setup") or []),
                      steps=steps, ties=raw.get("ties") or {}, sources=list(raw.get("sources") or []),
                      licence=raw.get("licence", "CC0-1.0"), raw=raw)


def all_storyboards() -> list[Storyboard]:
    return [load(p) for p in sorted(STORYBOARDS.glob("*.yaml"))]
