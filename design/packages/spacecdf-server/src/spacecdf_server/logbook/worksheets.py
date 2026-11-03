"""Worksheets offered in the logbook (LOGBOOK_SPEC.md §4).

Reads the generated worksheet YAML files in ``configs/worksheets/`` (every
file with a ``worksheets:`` list; ``worksheet_map.yaml`` is the hand-made
input to the generator and is skipped) and matches them to the context the
SpaceCDF frontend sends: wizard step, workbench tab, product-tree level and
V&V review gate.
"""
from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def worksheets_dir() -> Path:
    env = os.environ.get("SPACECDF_WORKSHEETS_DIR")
    if env:
        return Path(env)
    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "configs" / "worksheets"
        if cand.is_dir():
            return cand
    return here.parents[5] / "configs" / "worksheets"


@lru_cache(maxsize=4)
def _load(directory: str, stamp: tuple) -> tuple[dict, ...]:
    sheets: list[dict] = []
    for path in sorted(Path(directory).glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError) as e:
            logger.error("worksheets: cannot read %s: %s", path.name, e)
            continue
        items = data.get("worksheets") if isinstance(data, dict) else None
        if not isinstance(items, list) or not all(isinstance(w, dict) and "questions" in w for w in items):
            continue
        for order, w in enumerate(items):
            sheets.append({**w, "_file": path.name, "_order": order})
    return tuple(sheets)


def all_worksheets(directory: Path | None = None) -> tuple[dict, ...]:
    d = directory or worksheets_dir()
    try:
        stamp = tuple((p.name, p.stat().st_mtime_ns) for p in sorted(d.glob("*.yaml")))
    except OSError:
        return ()
    return _load(str(d), stamp)


def _tr(value: Any, lang: str) -> str:
    if isinstance(value, dict):
        return str(value.get(lang) or value.get("en") or "")
    return "" if value is None else str(value)


def _canon(gate: str) -> str:
    g = str(gate or "").strip().lower()
    return "mdr" if g == "mcr" else g   # MCR = the old name of MDR (ruling 3)


def _gate_ids(gate: str) -> set[str]:
    """Canonical gates a context gate stands for: itself, or those a merged profile gate
    covers (the ESA IOD concept review ``cr`` → mdr + prr)."""
    g = _canon(gate)
    out = {g}
    try:
        from ..services import gate_profiles as gp
        for p in gp.load().get("profiles", {}).values():
            for pg in p.get("gates") or []:
                if pg.get("id") == g and g not in gp.CANONICAL:
                    out |= set(pg.get("covers") or [])
    except Exception:  # noqa: BLE001
        pass
    return out


def match_score(ws: dict, tool: str, ctx: dict) -> int:
    """0 = not offered here; higher = more specific match."""
    ap = ws.get("applies") or {}
    if tool not in (ap.get("tools") or []):
        return 0
    step, tab, gate = ctx.get("step"), ctx.get("tab"), ctx.get("gate")
    level = ctx.get("level")
    try:
        level = int(level) if level is not None and level != "" else None
    except (TypeError, ValueError):
        level = None
    tabs, levels = ap.get("tabs") or [], ap.get("levels") or []
    score = 0
    if step and step in (ap.get("steps") or []):
        score = max(score, 3)
    if gate and _gate_ids(gate) & {_canon(g) for g in ap.get("gates") or []}:
        score = max(score, 3)
    if tab and tab in tabs:
        if not levels or level is None:
            score = max(score, 1)
        elif level in levels:
            score = max(score, 2)
    elif not tabs and level is not None and level in levels:
        score = max(score, 1)
    # ops-style keys, so the same YAML shape can carry ops worksheets too
    if ctx.get("page") and ctx["page"] in (ap.get("pages") or []):
        score = max(score, 2)
    if ctx.get("procedure") and ctx["procedure"] in (ap.get("procedures") or []):
        score = max(score, 3)
    return score


def localise(ws: dict, lang: str) -> dict:
    return {
        "id": ws.get("id"),
        "number": ws.get("number"),
        "title": _tr(ws.get("title"), lang),
        "phase": ws.get("phase") or "exercise",
        "applies": ws.get("applies") or {},
        "questions": [
            {"id": q.get("id"), "kind": q.get("kind") or "text",
             "text": _tr(q.get("text"), lang),
             "prompt": _tr(q.get("prompt"), lang) or None,
             "points": [_tr(p, lang) for p in (q.get("points") or [])]}
            for q in ws.get("questions") or []
        ],
    }


def for_context(tool: str, ctx: dict, lang: str, include_all: bool = False,
                directory: Path | None = None) -> list[dict]:
    out = []
    for ws in all_worksheets(directory):
        if tool not in ((ws.get("applies") or {}).get("tools") or []):
            continue
        score = match_score(ws, tool, ctx)
        if score == 0 and not include_all:
            continue
        item = localise(ws, lang)
        item["match"] = score > 0
        item["_score"] = score
        item["_order"] = ws["_order"]
        out.append(item)
    out.sort(key=lambda w: (-w["_score"], w["_order"]))
    for w in out:
        w.pop("_score")
        w.pop("_order")
    return out


def parts(directory: Path | None = None):
    """(worksheet id, lang) → [(question id, question text)] in workbook order."""
    sheets = {w.get("id"): w for w in all_worksheets(directory)}

    def _parts(wid: str, lang: str) -> list[tuple[str, str]]:
        ws = sheets.get(wid) or {}
        return [(str(q.get("id")), _tr(q.get("text"), lang)) for q in ws.get("questions") or []]
    return _parts


def lookup(directory: Path | None = None):
    """(worksheet id, question id, lang) → (title, question text, order) for exports."""
    sheets = {w.get("id"): w for w in all_worksheets(directory)}

    def _lookup(wid: str, qid: str, lang: str):
        ws = sheets.get(wid)
        if not ws:
            return None, None, 10_000
        for i, q in enumerate(ws.get("questions") or []):
            if q.get("id") == qid:
                return _tr(ws.get("title"), lang), _tr(q.get("text"), lang), i
        return _tr(ws.get("title"), lang), None, 10_000
    return _lookup
