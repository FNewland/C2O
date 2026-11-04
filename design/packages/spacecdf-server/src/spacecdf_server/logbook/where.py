"""Where a worksheet question or a decision is answered in SpaceCDF (Nov 2026 audit).

``configs/worksheets/where_map.yaml`` (hand-maintained) holds the vocabulary:

* ``targets``  id → a place in SpaceCDF (activity tab, level, section, anchor, V&V section,
  dialog or Mission Definition step) and the label the logbook shows (EN / FR);
* ``links``    id → an external open-access reference (https URL, optional French URL);
* ``parts``    worksheet question → target ids, textbook sections, link ids (copied into the
  generated ``learner_workbook.yaml`` by scripts/gen_worksheets.py);
* ``decisions`` catalogue decision → target ids and link ids (default: its workbook part's).

This module turns ids into the localised objects the frontend renders. A link whose URL is
not ``https://`` is dropped here as well as in the browser.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

import yaml

from .worksheets import worksheets_dir

logger = logging.getLogger(__name__)

WHERE_FILE = "where_map.yaml"
TARGET_KEYS = ("tab", "level", "domain", "section", "vv", "dialog", "wizard", "anchor")


@lru_cache(maxsize=4)
def _load(path: str, stamp: int) -> dict:
    try:
        return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as e:
        logger.error("where map: cannot read %s: %s", path, e)
        return {}


def where_map(directory: Path | None = None) -> dict:
    p = (directory or worksheets_dir()) / WHERE_FILE
    try:
        stamp = p.stat().st_mtime_ns
    except OSError:
        return {}
    return _load(str(p), stamp)


def _tr(value: Any, lang: str) -> str:
    if isinstance(value, dict):
        return str(value.get(lang) or value.get("en") or "")
    return "" if value is None else str(value)


def targets(ids: Iterable[str] | None, lang: str, directory: Path | None = None) -> list[dict]:
    """Target ids → [{id, label, tab?, level?, …}] (unknown ids are skipped)."""
    known = where_map(directory).get("targets") or {}
    out = []
    for tid in ids or []:
        t = known.get(tid)
        if not isinstance(t, dict):
            continue
        item = {"id": tid, "label": _tr(t.get("label"), lang)}
        for k in TARGET_KEYS:
            if t.get(k) is not None:
                item[k] = t[k]
        out.append(item)
    return out


def links(ids: Iterable[str] | None, lang: str, directory: Path | None = None) -> list[dict]:
    """Link ids → [{id, title, url, lang}]: the French URL in French when there is one."""
    known = where_map(directory).get("links") or {}
    out = []
    for lid in ids or []:
        ln = known.get(lid)
        if not isinstance(ln, dict):
            continue
        url_fr = ln.get("url_fr") if lang == "fr" else None
        url = str(url_fr or ln.get("url") or "")
        if not url.startswith("https://"):
            continue
        out.append({"id": lid, "title": _tr(ln.get("title"), lang), "url": url,
                    "lang": "fr" if url_fr else "en"})
    return out


def book(refs: Iterable[str] | None) -> list[str]:
    return [str(r) for r in refs or []]


def for_question(q: dict, lang: str, directory: Path | None = None) -> dict:
    """The where / links / book fields a localised worksheet question carries."""
    return {"where": targets(q.get("where"), lang, directory),
            "links": links(q.get("links"), lang, directory),
            "book": book(q.get("book"))}


def for_decision(decision_id: str, part: str | None, lang: str, directory: Path | None = None) -> dict:
    """A decision's where / links / book: its own entry, else its workbook part's."""
    wm = where_map(directory)
    own = (wm.get("decisions") or {}).get(decision_id) or {}
    part_entry = (wm.get("parts") or {}).get(part or "") or {}
    return {"where": targets(own.get("where") or part_entry.get("where"), lang, directory),
            "links": links(own.get("links") or part_entry.get("links"), lang, directory),
            "book": book(own.get("book") or part_entry.get("book"))}
