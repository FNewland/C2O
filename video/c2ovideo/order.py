"""The term order of the course videos (``video/course_order.yaml``): week, position, week titles."""

from __future__ import annotations

from functools import lru_cache

import yaml

from .storyboard import ROOT

FILE = ROOT / "course_order.yaml"


@lru_cache(maxsize=1)
def _load() -> dict:
    raw = yaml.safe_load(FILE.read_text(encoding="utf-8")) or {}
    weeks, place = [], {}
    for w in raw.get("weeks") or []:
        weeks.append({"week": int(w["week"]), "title": w.get("title") or {}})
        for vid in w.get("videos") or []:
            if vid in place:
                raise ValueError(f"{vid} is listed twice in {FILE.name}")
            place[vid] = (int(w["week"]), len(place))
    return {"weeks": weeks, "place": place}


def weeks() -> list[dict]:
    """[{week, title: {en, fr}}] in term order."""
    return _load()["weeks"]


def place(video_id: str) -> tuple[int, int] | None:
    """(week, position in the term) of a video, or None when it is not listed."""
    return _load()["place"].get(video_id)


def problems(storyboards) -> list[str]:
    """Every storyboard listed once, under the week its own ``week:`` names; nothing unknown listed."""
    out, ids = [], set()
    for sb in storyboards:
        ids.add(sb.id)
        p = place(sb.id)
        if p is None:
            out.append(f"{sb.id}: not listed in {FILE.name}")
        elif sb.week != p[0]:
            out.append(f"{sb.id}: storyboard says week {sb.week}, {FILE.name} lists it in week {p[0]}")
    for vid in _load()["place"]:
        if vid not in ids:
            out.append(f"{vid}: listed in {FILE.name} but has no storyboard")
    return out


def sort_catalog(cat: dict) -> dict:
    """Put the term order (week, position, week titles) into a published catalogue."""
    for v in cat.get("videos", []):
        p = place(v["id"])
        if p:
            v["week"], v["order"] = p
        else:
            v["order"] = 10_000
    cat["videos"].sort(key=lambda v: (v.get("week") or 99, v.get("order", 10_000), v["id"]))
    cat["weeks"] = weeks()
    return cat
