"""Design decisions: the catalogue and the structured decision record.

The catalogue (``configs/worksheets/decision_catalogue.yaml``, hand-maintained)
lists the decisions the learner workbook asks a team to make, each tied to a
workbook part, an owning seat and the review gate it must be recorded by.

A decision record is a logbook entry of ``kind: "decision"`` with three
optional additions to the shared record format (LOGBOOK_SPEC.md §2). All three
are safe for the ops tools' implementation to ignore:

``record``            the structured record (shape below), on ``add`` and
                      ``edit`` records. smo-common folds only the fields it
                      knows, so it never sees this one.
``context.decision_id``  the catalogue id, as a plain context value (smo-common
                      keeps context through its compaction, so the "recorded"
                      status survives even there).
``worksheet``         ``{id, q, title, q_text, section: "decision"}``: the
                      workbook part, the same object worksheet answers carry.

``text`` is always a complete plain-text rendering of the record (built here,
never by the browser), so every export, the ops tools' included, prints the
whole decision even where ``record`` is unknown.

Record shape (every field optional except ``decision_id``)::

    {"v": 1, "decision_id": "D-2.3-ORBIT", "subject": "…",
     "question": "…", "part": "LW-2.3/B", "part_title": "…", "gate": "prr", "seat": "mission_analyst",
     "options":  [{"name": "SSO 550 km", "summary": "…", "values": {"GSD (m)": 4.1}, "score": 0.85, "chosen": true}],
     "criteria": [{"name": "GSD", "weight": 0.4, "direction": "lower"}],
     "choice": "…", "rationale": "…",
     "evidence": [{"label": "Altitude", "value": 550, "unit": "km", "before": 500, "after": 550}],
     "consequences": "…", "margin_impact": "…", "open_issues": "…",
     "capture": "decide:orbit-trade"}
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

import yaml

from .store import LogbookError
from .worksheets import worksheets_dir

logger = logging.getLogger(__name__)

CATALOGUE_FILE = "decision_catalogue.yaml"
GATE_ORDER = ("mdr", "prr", "srr", "pdr")
FIELDS = ("options", "criteria", "choice", "rationale", "evidence", "consequences", "margin_impact", "open_issues")
TEXT_FIELDS = {"choice": 1_000, "rationale": 4_000, "consequences": 4_000, "margin_impact": 1_000,
               "open_issues": 2_000, "subject": 200, "question": 500, "part_title": 300}
RECORD_LIMIT = 16_384      # bytes of JSON per record
MAX_OPTIONS = 20
MAX_CRITERIA = 12
MAX_EVIDENCE = 30
MAX_VALUES = 12


# ─── Catalogue ────────────────────────────────────────────────────────────

def catalogue_path(directory: Path | None = None) -> Path:
    return (directory or worksheets_dir()) / CATALOGUE_FILE


@lru_cache(maxsize=4)
def _load(path: str, stamp: int) -> dict:
    try:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as e:
        logger.error("decision catalogue: cannot read %s: %s", path, e)
        return {"gates": [], "seats": [], "fields": {}, "sources": {}, "decisions": []}
    return data


def catalogue(directory: Path | None = None) -> dict:
    p = catalogue_path(directory)
    try:
        stamp = p.stat().st_mtime_ns
    except OSError:
        return {"gates": [], "seats": [], "fields": {}, "sources": {}, "decisions": []}
    return _load(str(p), stamp)


def _tr(value: Any, lang: str) -> str:
    if isinstance(value, dict):
        return str(value.get(lang) or value.get("en") or "")
    return "" if value is None else str(value)


def by_id(directory: Path | None = None) -> dict[str, dict]:
    return {d["id"]: d for d in catalogue(directory).get("decisions") or []}


def gate_of_ui(ui_gate: str | None, directory: Path | None = None) -> str | None:
    """A gate id from the UI (``mcr`` is the old MDR) → the catalogue gate id."""
    if not ui_gate:
        return None
    g = ui_gate.lower()
    for gate in catalogue(directory).get("gates") or []:
        if g == gate["id"] or g in (gate.get("ui_gates") or []):
            return gate["id"]
    return None


def due_by(gate: str) -> set[str]:
    """Gates whose decisions must be recorded by ``gate`` (cumulative)."""
    if gate not in GATE_ORDER:
        return set()
    return set(GATE_ORDER[: GATE_ORDER.index(gate) + 1])


# ─── Record validation ────────────────────────────────────────────────────

def _scalar(v: Any, limit: int = 200) -> str | int | float | bool | None:
    if v is None or isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v if v == v and abs(v) != float("inf") else None   # no NaN / inf
    if isinstance(v, str):
        return v.strip()[:limit]
    return str(v)[:limit]


def _text(v: Any, limit: int) -> str:
    if not isinstance(v, str):
        return ""
    return v.replace("\r\n", "\n").strip()[:limit]


def clean_record(rec: Any) -> dict | None:
    """Validate the structured record; unknown keys are dropped. None = no record."""
    if rec is None:
        return None
    if not isinstance(rec, dict):
        raise LogbookError(400, "record must be an object")
    did = rec.get("decision_id")
    if not isinstance(did, str) or not did.strip() or len(did) > 64:
        raise LogbookError(400, "record.decision_id must be a short string")
    out: dict[str, Any] = {"v": 1, "decision_id": did.strip()}
    for k in ("part", "gate", "seat", "capture"):
        if isinstance(rec.get(k), str) and rec[k].strip():
            out[k] = rec[k].strip()[:64]
    for k, limit in TEXT_FIELDS.items():
        t = _text(rec.get(k), limit)
        if t:
            out[k] = t

    opts = rec.get("options")
    if opts is not None:
        if not isinstance(opts, list):
            raise LogbookError(400, "record.options must be a list")
        clean = []
        for o in opts[:MAX_OPTIONS]:
            if not isinstance(o, dict):
                continue
            name = _text(o.get("name"), 200)
            if not name:
                continue
            item: dict[str, Any] = {"name": name}
            summary = _text(o.get("summary"), 500)
            if summary:
                item["summary"] = summary
            vals = o.get("values")
            if isinstance(vals, dict):
                v2 = {str(k)[:60]: _scalar(v) for k, v in list(vals.items())[:MAX_VALUES]
                      if _scalar(v) not in (None, "")}
                if v2:
                    item["values"] = v2
            score = _scalar(o.get("score"))
            if isinstance(score, (int, float)) and not isinstance(score, bool):
                item["score"] = score
            if o.get("chosen") is True:
                item["chosen"] = True
            clean.append(item)
        if clean:
            out["options"] = clean

    crit = rec.get("criteria")
    if crit is not None:
        if not isinstance(crit, list):
            raise LogbookError(400, "record.criteria must be a list")
        clean = []
        for c in crit[:MAX_CRITERIA]:
            if not isinstance(c, dict):
                continue
            name = _text(c.get("name"), 100)
            if not name:
                continue
            item = {"name": name}
            w = _scalar(c.get("weight"))
            if isinstance(w, (int, float)) and not isinstance(w, bool):
                item["weight"] = w
            if c.get("direction") in ("higher", "lower"):
                item["direction"] = c["direction"]
            clean.append(item)
        if clean:
            out["criteria"] = clean

    ev = rec.get("evidence")
    if ev is not None:
        if not isinstance(ev, list):
            raise LogbookError(400, "record.evidence must be a list")
        clean = []
        for e in ev[:MAX_EVIDENCE]:
            if not isinstance(e, dict):
                continue
            label = _text(e.get("label"), 120)
            if not label:
                continue
            item = {"label": label}
            for k in ("value", "before", "after"):
                v = _scalar(e.get(k))
                if v not in (None, ""):
                    item[k] = v
            unit = _text(e.get("unit"), 20)
            if unit:
                item["unit"] = unit
            clean.append(item)
        if clean:
            out["evidence"] = clean

    if len(json.dumps(out, ensure_ascii=False).encode("utf-8")) > RECORD_LIMIT:
        raise LogbookError(413, "The decision record is too large.")
    return out


def has_content(rec: dict) -> bool:
    """Something the student wrote or chose beyond the catalogue's own text."""
    return any(rec.get(k) for k in ("choice", "rationale", "options", "evidence", "consequences",
                                    "margin_impact", "open_issues", "criteria"))


# ─── Labels and plain-text rendering ──────────────────────────────────────

_L: dict[str, dict[str, str]] = {
    "decision": {"en": "Decision", "fr": "Décision"},
    "chosen": {"en": "chosen", "fr": "retenue"},
    "score": {"en": "score", "fr": "score"},
    "higher": {"en": "higher is better", "fr": "plus élevé = meilleur"},
    "lower": {"en": "lower is better", "fr": "plus bas = meilleur"},
    "weight": {"en": "weight", "fr": "poids"},
    "gate": {"en": "Gate", "fr": "Jalon"},
    "seat": {"en": "Owner", "fr": "Responsable"},
    "part": {"en": "Workbook", "fr": "Cahier"},
    "subject": {"en": "Subject", "fr": "Objet"},
    "option": {"en": "Option", "fr": "Option"},
}
NBSP = " "


def lab(key: str, lang: str) -> str:
    return _L[key].get(lang) or _L[key]["en"]


def colon(lang: str) -> str:
    return f"{NBSP}:" if lang == "fr" else ":"


def field_label(name: str, lang: str, directory: Path | None = None) -> str:
    return _tr((catalogue(directory).get("fields") or {}).get(name), lang) or name


def seat_label(seat: str | None, lang: str, directory: Path | None = None) -> str:
    for s in catalogue(directory).get("seats") or []:
        if s["id"] == seat:
            return _tr(s.get("label"), lang)
    return seat or ""


def gate_label(gate: str | None, lang: str, directory: Path | None = None) -> str:
    for g in catalogue(directory).get("gates") or []:
        if g["id"] == gate:
            return _tr(g.get("label"), lang)
    return (gate or "").upper()


def fmt_value(v: Any, lang: str = "en") -> str:
    if isinstance(v, bool):
        return "✓" if v else "✗"
    if isinstance(v, float):
        s = f"{v:.4g}" if abs(v) < 1e6 else f"{v:.3e}"
        return s.replace(".", ",") if lang == "fr" else s
    return str(v)


def evidence_text(e: dict, lang: str) -> str:
    unit = f"{NBSP}{e['unit']}" if e.get("unit") else ""
    if "before" in e or "after" in e:
        b = fmt_value(e.get("before"), lang) + unit if "before" in e else "—"
        a = fmt_value(e.get("after", e.get("value")), lang) + unit if ("after" in e or "value" in e) else "—"
        return f"{e['label']}{colon(lang)} {b} → {a}"
    if "value" in e:
        return f"{e['label']}{colon(lang)} {fmt_value(e['value'], lang)}{unit}"
    return e["label"]


def option_values_text(o: dict, lang: str) -> str:
    bits = [f"{k} {fmt_value(v, lang)}" for k, v in (o.get("values") or {}).items()]
    if "score" in o:
        s = o["score"]
        bits.append(f"{lab('score', lang)} {fmt_value(round(s * 100) if isinstance(s, float) and s <= 1 else s, lang)}"
                    + ("%" if isinstance(s, float) and s <= 1 else ""))
    return ", ".join(bits)


def criterion_text(c: dict, lang: str) -> str:
    bits = []
    if "weight" in c:
        bits.append(f"{lab('weight', lang)} {fmt_value(c['weight'], lang)}")
    if c.get("direction"):
        bits.append(lab(c["direction"], lang))
    return c["name"] + (f" ({', '.join(bits)})" if bits else "")


def render_text(rec: dict, lang: str, directory: Path | None = None) -> str:
    """The whole record as plain text: the entry's ``text`` (read by every export)."""
    cat = by_id(directory).get(rec["decision_id"], {})
    q = rec.get("question") or _tr(cat.get("question"), lang)
    c = colon(lang)
    L = [f"{lab('decision', lang)} {rec['decision_id']}" + (f" — {q}" if q else "")]
    if rec.get("subject"):
        L.append(f"{lab('subject', lang)}{c} {rec['subject']}")
    if rec.get("choice"):
        L.append(f"{field_label('choice', lang, directory)}{c} {rec['choice']}")
    if rec.get("options"):
        L.append(f"{field_label('options', lang, directory)}{c}")
        for o in rec["options"]:
            vals = option_values_text(o, lang)
            mark = f" [{lab('chosen', lang)}]" if o.get("chosen") else ""
            L.append(f"- {o['name']}{mark}" + (f" ({vals})" if vals else "") + (f" — {o['summary']}" if o.get("summary") else ""))
    if rec.get("criteria"):
        L.append(f"{field_label('criteria', lang, directory)}{c} " + "; ".join(criterion_text(x, lang) for x in rec["criteria"]))
    for k in ("rationale",):
        if rec.get(k):
            L.append(f"{field_label(k, lang, directory)}{c} {rec[k]}")
    if rec.get("evidence"):
        L.append(f"{field_label('evidence', lang, directory)}{c}")
        L.extend(f"- {evidence_text(e, lang)}" for e in rec["evidence"])
    for k in ("consequences", "margin_impact", "open_issues"):
        if rec.get(k):
            L.append(f"{field_label(k, lang, directory)}{c} {rec[k]}")
    meta = []
    if rec.get("part"):
        meta.append(f"{lab('part', lang)} {rec['part']}")
    if rec.get("gate"):
        meta.append(f"{lab('gate', lang)} {rec['gate'].upper()}")
    if rec.get("seat"):
        meta.append(f"{lab('seat', lang)} {seat_label(rec['seat'], lang, directory)}")
    if meta:
        L.append(" · ".join(meta))
    return "\n".join(L)[:8_000]


def complete(rec: dict, lang: str, lookup=None, directory: Path | None = None) -> dict:
    """Fill the catalogue facts the browser need not send (question, part, gate, seat)."""
    cat = by_id(directory).get(rec["decision_id"])
    if not cat:
        return rec
    rec = dict(rec)
    rec.setdefault("question", _tr(cat.get("question"), lang))
    rec.setdefault("part", cat.get("part"))
    rec.setdefault("gate", cat.get("gate"))
    rec.setdefault("seat", cat.get("seat"))
    if lookup and "part_title" not in rec and rec.get("part") and "/" in rec["part"]:
        wid, qid = rec["part"].split("/", 1)
        _, qtext, _ = lookup(wid, qid, lang)
        if qtext:
            rec["part_title"] = qtext
    return rec


def worksheet_ref(rec: dict, lang: str, lookup=None) -> dict | None:
    """The ``worksheet`` object a decision entry carries: its workbook part."""
    part = rec.get("part")
    if not part or "/" not in part:
        return None
    wid, qid = part.split("/", 1)
    ref = {"id": wid, "q": qid, "section": "decision"}
    if lookup:
        title, qtext, _ = lookup(wid, qid, lang)
        if title:
            ref["title"] = title
        if qtext:
            ref["q_text"] = qtext
    return ref


# ─── Status (per person, per study) ───────────────────────────────────────

def decision_id_of(entry: dict) -> str | None:
    rec = entry.get("record")
    if isinstance(rec, dict) and isinstance(rec.get("decision_id"), str):
        return rec["decision_id"]
    did = (entry.get("context") or {}).get("decision_id")
    return did if isinstance(did, str) else None


def recorded(entries: Iterable[dict], study_id: str | None) -> dict[str, list[dict]]:
    """decision id → this person's decision entries for this study, newest first.

    Entries written before a study existed (the mission wizard) carry no
    study id and count for any study.
    """
    out: dict[str, list[dict]] = {}
    for e in sorted(entries, key=lambda e: e.get("ts") or "", reverse=True):
        if e.get("kind") != "decision":
            continue
        did = decision_id_of(e)
        if not did:
            continue
        sid = (e.get("context") or {}).get("study_id")
        if study_id and sid and sid != study_id:
            continue
        out.setdefault(did, []).append(e)
    return out


def localised(lang: str, entries: Iterable[dict], study_id: str | None, lookup=None,
              directory: Path | None = None) -> dict:
    """The catalogue in ``lang`` with this person's status, for GET /api/logbook/decisions."""
    cat = catalogue(directory)
    rec = recorded(entries, study_id)
    gates = [{"id": g["id"], "label": _tr(g.get("label"), lang), "ui_gates": g.get("ui_gates") or []}
             for g in cat.get("gates") or []]
    seats = [{"id": s["id"], "label": _tr(s.get("label"), lang)} for s in cat.get("seats") or []]
    fields = {k: _tr(v, lang) for k, v in (cat.get("fields") or {}).items()}
    sources = {k: {"label": _tr(v.get("label"), lang), "server": bool(v.get("server"))}
               for k, v in (cat.get("sources") or {}).items()}
    order = {}
    for i, d in enumerate(cat.get("decisions") or []):
        order[d["id"]] = i
    items = []
    for d in cat.get("decisions") or []:
        wid, qid = (d["part"].split("/", 1) + [""])[:2]
        ws_title = q_text = None
        q_order = 10_000
        if lookup:
            ws_title, q_text, q_order = lookup(wid, qid, lang)
        mine = rec.get(d["id"], [])
        items.append({
            "id": d["id"],
            "part": d["part"],
            "worksheet": wid,
            "q": qid,
            "worksheet_title": ws_title,
            "part_title": q_text,
            "question": _tr(d.get("question"), lang),
            "hint": _tr(d.get("hint"), lang) or None,
            "seat": d["seat"],
            "seat_label": seat_label(d["seat"], lang, directory),
            "gate": d["gate"],
            "fields": d.get("fields") or [],
            "prefill": d.get("prefill") or [],
            "capture": d.get("capture") or [],
            "entries": [e["id"] for e in mine],
            "status": "recorded" if mine else "open",
            "_wnum": _wnum(wid), "_q": q_order, "_i": order[d["id"]],
        })
    items.sort(key=lambda x: (x["_wnum"], x["_q"], x["_i"]))
    for x in items:
        for k in ("_wnum", "_q", "_i"):
            x.pop(k)
    counts = {g["id"]: {"total": 0, "open": 0} for g in gates}
    for x in items:
        c = counts.setdefault(x["gate"], {"total": 0, "open": 0})
        c["total"] += 1
        c["open"] += x["status"] == "open"
    return {"lang": lang, "study_id": study_id, "gates": gates, "seats": seats, "fields": fields,
            "sources": sources, "decisions": items, "counts": counts}


def _wnum(wid: str) -> tuple:
    try:
        a, b = wid.split("-", 1)[1].split(".")
        return (int(a), int(b))
    except (IndexError, ValueError):
        return (99, 99)
