"""Course-workbook worksheets offered in the logbook (LOGBOOK_SPEC §4).

The YAML is generated from the workbook by ``tools/gen_worksheets.py``
(``configs/eosat1/worksheets/ops_week3.yaml``); ``worksheet_map.yaml`` next
to it is that script's input and is not read here.

Matching a context (``match``): a worksheet is offered by a tool when the
tool is in ``applies.tools`` and
  * it names procedures / pages / scenarios and the context's
    ``procedure`` / ``page`` / ``scenario`` is one of them, or
  * it names none of those (a general worksheet for the tool).
A ``phase`` in the context keeps only worksheets of that phase. Results are
ordered procedure > page > scenario > context key > general, then by file
order, and say why they matched (``match``).
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

__all__ = ["WorksheetCatalog", "default_worksheets_dir"]

_RANK = {"procedure": 0, "page": 1, "scenario": 2, "context": 3, "general": 4}
_MAP_FILE = "worksheet_map.yaml"


def default_worksheets_dir() -> Path | None:
    env = os.environ.get("SMO_WORKSHEETS_DIR", "").strip()
    cands = [Path(env)] if env else []
    cands += [Path("configs") / "eosat1" / "worksheets",
              Path(__file__).resolve().parents[5] / "configs" / "eosat1" / "worksheets"]
    for c in cands:
        if c.is_dir():
            return c
    return None


def _loc(v: Any, lang: str) -> str:
    if isinstance(v, dict):
        return str(v.get(lang) or v.get("en") or "")
    return "" if v is None else str(v)


class WorksheetCatalog:
    def __init__(self, directory: str | os.PathLike | None = None):
        self.dir = Path(directory) if directory else default_worksheets_dir()
        self._stamp: tuple | None = None
        self._sheets: list[dict] = []

    def _files(self) -> list[Path]:
        if not self.dir or not self.dir.is_dir():
            return []
        return sorted(p for p in self.dir.glob("*.yaml") if p.name != _MAP_FILE)

    def sheets(self) -> list[dict]:
        files = self._files()
        stamp = tuple((p.name, p.stat().st_mtime_ns) for p in files)
        if stamp != self._stamp:
            sheets = []
            for p in files:
                try:
                    doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
                except (OSError, yaml.YAMLError) as e:
                    logger.warning("worksheets: cannot read %s: %s", p, e)
                    continue
                for w in doc.get("worksheets") or []:
                    if isinstance(w, dict) and w.get("id"):
                        sheets.append(w)
            self._sheets, self._stamp = sheets, stamp
        return self._sheets

    def get(self, wid: str) -> dict | None:
        return next((w for w in self.sheets() if w.get("id") == wid), None)

    def question(self, wid: str, qid: str, lang: str = "en") -> tuple[str, str] | None:
        """(worksheet title, question text) in *lang*, for exports."""
        w = self.get(wid)
        if not w:
            return None
        q = next((q for q in w.get("questions") or [] if q.get("id") == qid), None)
        return _loc(w.get("title"), lang), _loc(q.get("text"), lang) if q else ""

    @staticmethod
    def _why(w: dict, tool: str, ctx: dict) -> str | None:
        ap = w.get("applies") or {}
        if tool not in (ap.get("tools") or []):
            return None
        procs, pages, scns = (ap.get("procedures") or [], ap.get("pages") or [],
                              ap.get("scenarios") or [])
        if procs or pages or scns:
            if ctx.get("procedure") in procs:
                return "procedure"
            if ctx.get("page") in pages:
                return "page"
            if ctx.get("scenario") in scns:
                return "scenario"
            return None
        if any(ctx.get(k) not in (None, "", False) for k in ap.get("context_keys") or []):
            return "context"
        return "general"

    def match(self, tool: str, context: dict | None = None, lang: str = "en") -> list[dict]:
        ctx = context if isinstance(context, dict) else {}
        lang = "fr" if lang == "fr" else "en"
        phase = ctx.get("phase")
        out = []
        for order, w in enumerate(self.sheets()):
            why = self._why(w, tool, ctx)
            if why is None or (phase and w.get("phase") != phase):
                continue
            out.append((_RANK[why], order, self.localise(w, lang, why)))
        out.sort(key=lambda t: (t[0], t[1]))
        return [w for _, _, w in out]

    @staticmethod
    def localise(w: dict, lang: str, why: str | None = None) -> dict:
        qs = []
        for q in w.get("questions") or []:
            item = {"id": q.get("id"), "kind": q.get("kind") or "text",
                    "text": _loc(q.get("text"), lang)}
            if q.get("hint"):
                item["hint"] = _loc(q["hint"], lang)
            if q.get("section"):
                item["section"] = _loc(q["section"], lang)
            qs.append(item)
        out = {"id": w.get("id"), "title": _loc(w.get("title"), lang),
               "phase": w.get("phase"), "applies": w.get("applies") or {},
               "questions": qs}
        if why:
            out["match"] = why
        return out
