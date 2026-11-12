"""Copy rendered videos into the folder the C2O welcome page serves.

Layout of the video folder (``SMO_VIDEO_DIR``, default ``sim/workspace/videos``)::

    catalog.json                 every published video, both languages
    h5p-libraries/               H5P runtime libraries, shared by all players
    <slug>/<slug>.<lang>.mp4|vtt|chapters.vtt|poster.jpg|transcript.md|h5p
    <slug>/h5p/<lang>/           unpacked package for the in-tool player
    <slug>/review/               narration review (instructors only)
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from . import LANGS, h5p, order, worksheets
from .storyboard import REPO, Storyboard, tr

DEFAULT_DIR = REPO / "sim" / "workspace" / "videos"


def video_dir() -> Path:
    return Path(os.environ.get("SMO_VIDEO_DIR", DEFAULT_DIR))


def entry(sb: Storyboard, media: Path) -> dict:
    langs = {}
    for lang in LANGS:
        meta_f = media / f"{sb.slug}.{lang}.json"
        if not meta_f.exists():
            continue
        meta = json.loads(meta_f.read_text(encoding="utf-8"))
        langs[lang] = {"mp4": f"{sb.slug}.{lang}.mp4", "vtt": f"{sb.slug}.{lang}.vtt",
                       "chapters": f"{sb.slug}.{lang}.chapters.vtt", "poster": f"{sb.slug}.{lang}.poster.jpg",
                       "transcript": f"{sb.slug}.{lang}.transcript.md", "h5p": f"{sb.slug}.{lang}.h5p",
                       "duration": meta["duration"], "chapter_list": meta["chapters"],
                       "questions": len(meta["questions"]),
                       "question_list": [
                           {"step": st.id, "subContentId": h5p.sub_id(sb, lang, st.id),
                            "text": tr(st.question["text"], lang), "worksheet": st.question.get("worksheet") or "",
                            "worksheet_label": worksheets.label(st.question["worksheet"], lang) if st.question.get("worksheet") else ""}
                           for st in sb.steps if st.question]}
    ties = []
    for t in (sb.ties.get("worksheets") or []) + (sb.ties.get("decisions") or []):
        r = worksheets.resolve(t)
        ties.append({"id": t, "tool": r["worksheet"]["tool"], "label": {l: worksheets.label(t, l) for l in LANGS}})
    return {"id": sb.id, "slug": sb.slug, "week": sb.week, "title": sb.title, "summary": sb.summary,
            "ties": ties, "cards": sb.ties.get("cards") or [], "audience": sb.raw.get("audience", "all"),
            "langs": langs, "licence": "CC0-1.0",
            "published": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}


def publish(sb: Storyboard, media: Path, dest: Path | None = None) -> Path:
    dest = dest or video_dir()
    dest.mkdir(parents=True, exist_ok=True)
    h5p.export_libraries(dest / "h5p-libraries")
    target = dest / sb.slug
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(media, target, symlinks=True,
                    ignore=shutil.ignore_patterns("*.json.tmp", "take-*", "frames", "*.ffconcat"))
    cat_f = dest / "catalog.json"
    cat = json.loads(cat_f.read_text(encoding="utf-8")) if cat_f.exists() else {"videos": []}
    cat["videos"] = [v for v in cat["videos"] if v["id"] != sb.id] + [entry(sb, media)]
    order.sort_catalog(cat)
    write_catalog(cat_f, cat)
    return target


def write_catalog(cat_f: Path, cat: dict) -> None:
    tmp = cat_f.with_suffix(".tmp")
    tmp.write_text(json.dumps(cat, indent=1, ensure_ascii=False), encoding="utf-8")
    tmp.replace(cat_f)


def resort(dest: Path | None = None) -> Path:
    """Re-apply the term order to the published catalogue (no media is touched)."""
    cat_f = (dest or video_dir()) / "catalog.json"
    cat = json.loads(cat_f.read_text(encoding="utf-8"))
    write_catalog(cat_f, order.sort_catalog(cat))
    return cat_f
