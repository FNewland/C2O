"""Logbook export: Markdown, print-ready HTML and JSON (LOGBOOK_SPEC.md §3).

The download reads like a completed learner workbook:

1. **Workbook** — worksheets in workbook order, each part in order, holding
   its decision records (structured blocks: question, options table,
   criteria, choice, rationale, evidence, consequences…) and the worksheet
   answers, with the part's decisions not yet recorded listed under it;
2. **Open decisions** — catalogue decisions without a record, by gate;
3. **Log** — everything else (free entries, every tool), by day, tool, time.

``worksheet=<id>`` renders one worksheet alone, every part listed ("Download
this worksheet", "Copy as Markdown"). Both document formats carry a header
(person, export time, tools used, entry count) and the full export the
footer "Deleted from the C2O server on <expires_at>".

Times print in the participant's time zone when the UI sends one (``tz``,
an IANA name such as ``America/Toronto``), else in UTC; the day grouping
follows the same zone so an evening session is not split at midnight UTC.

The HTML is self-contained (no scripts, no external files) and prints on A4
or Letter, so "Save as PDF" in the browser gives the PDF.
"""
from __future__ import annotations

import html
import json
import re
from collections import OrderedDict
from datetime import datetime, timezone, tzinfo
from typing import Any, Callable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .store import parse_ts

NBSP = " "

# Export strings. French follows the C2O house style (STYLE_FR.md):
# U+00A0 before ':' and between a number and its unit.
_S: dict[str, dict[str, str]] = {
    "title": {"en": "C2O logbook", "fr": "Journal de bord C2O"},
    "person": {"en": "Person", "fr": "Personne"},
    "exported": {"en": "Exported", "fr": "Exporté le"},
    "tools": {"en": "Tools", "fr": "Outils"},
    "tz": {"en": "Times in", "fr": "Heures en"},
    "entries": {"en": "Entries", "fr": "Entrées"},
    "none": {"en": "No entries.", "fr": "Aucune entrée."},
    "this_browser": {"en": "this browser", "fr": "ce navigateur"},
    "worksheets": {"en": "Worksheets", "fr": "Fiches"},
    "edited": {"en": "edited {t}", "fr": f"modifiée à {{t}}"},
    "sim": {"en": "sim time {t}", "fr": f"temps simulé {{t}}"},
    "context": {"en": "Context", "fr": "Contexte"},
    "footer": {"en": "Deleted from the C2O server on {t} ({h} h after the last entry). "
                     "This copy is yours to keep.",
               "fr": f"Supprimé du serveur C2O le {{t}} ({{h}}{NBSP}h après la dernière entrée). "
                     "Cette copie est à vous."},
    "footer_none": {"en": "Nothing is stored on the C2O server.",
                    "fr": "Rien n’est conservé sur le serveur C2O."},
    "private": {"en": "Private to the participant. The instructor never sees this text unless you hand it in.",
                "fr": "Réservé à la personne participante. L’instructeur ne voit jamais ce texte, sauf si vous le remettez."},
    # Workbook layout (decision records, worksheets, open decisions, free log)
    "workbook": {"en": "Workbook", "fr": "Cahier d’exercices"},
    "worksheet": {"en": "Worksheet", "fr": "Fiche"},
    "log": {"en": "Log", "fr": "Journal"},
    "decisions": {"en": "Decisions", "fr": "Décisions"},
    "decisions_count": {"en": "{n} recorded · {o} still open", "fr": "{n} consignées · {o} encore ouvertes"},
    "open_decisions": {"en": "Open decisions", "fr": "Décisions ouvertes"},
    "open_help": {"en": "Decisions from the workbook you have not recorded yet, by the review that needs them.",
                  "fr": "Décisions du cahier d’exercices que vous n’avez pas encore consignées, classées par revue."},
    "open_here": {"en": "Not recorded yet", "fr": "Pas encore consignées"},
    "answers": {"en": "Worksheet answers", "fr": "Réponses à la fiche"},
    "owner": {"en": "owner", "fr": "responsable"},
    "by_gate": {"en": "by {g}", "fr": "avant la {g}"},
    "recorded": {"en": "recorded {t}", "fr": "consignée le {t}"},
    "subject": {"en": "Subject", "fr": "Objet"},
    "option": {"en": "Option", "fr": "Option"},
    "values": {"en": "Values", "fr": "Valeurs"},
    "score": {"en": "Score", "fr": "Score"},
    "chosen": {"en": "chosen", "fr": "retenue"},
}

KIND_LABEL = {
    "decision": {"en": "Decision", "fr": "Décision"},
    "thought": {"en": "Thought", "fr": "Idée"},
    "observation": {"en": "Observation", "fr": "Observation"},
    "reflection": {"en": "Reflection", "fr": "Réflexion"},
    "worksheet": {"en": "Worksheet", "fr": "Fiche"},
}

TOOL_LABEL = {
    "design": {"en": "SpaceCDF (design)", "fr": "SpaceCDF (conception)"},
    "mcs": {"en": "Mission control (MCS)", "fr": "Contrôle de mission (MCS)"},
    "delayed_tm": {"en": "Delayed TM", "fr": "TM différée"},
    "orbit": {"en": "Orbit", "fr": "Orbite"},
    "radio": {"en": "Radio", "fr": "Radio"},
    "docs": {"en": "Documents", "fr": "Documents"},
    "instructor": {"en": "Instructor", "fr": "Instructeur"},
    "portal": {"en": "Portal", "fr": "Portail"},
}

# Context keys: the spec's ops keys plus SpaceCDF's. Unknown keys print as-is.
CONTEXT_LABEL = {
    "study_name": {"en": "study", "fr": "étude"},
    "study_id": {"en": "study id", "fr": "id d’étude"},
    "step": {"en": "step", "fr": "étape"},
    "tab": {"en": "tab", "fr": "onglet"},
    "level": {"en": "level", "fr": "niveau"},
    "element": {"en": "element", "fr": "élément"},
    "gate": {"en": "gate", "fr": "revue"},
    "decision": {"en": "on", "fr": "sur"},
    "page": {"en": "page", "fr": "page"},
    "procedure": {"en": "procedure", "fr": "procédure"},
    "alarm_id": {"en": "alarm", "fr": "alarme"},
    "param": {"en": "parameter", "fr": "paramètre"},
    "position": {"en": "position", "fr": "poste"},
    "scenario": {"en": "scenario", "fr": "scénario"},
}
# SpaceCDF context values that are ids: printed as words.
TAB_LABEL = {
    "blocks": {"en": "Blocks", "fr": "Blocs"}, "spacecraft": {"en": "Spacecraft", "fr": "Véhicule spatial"},
    "budget": {"en": "Budget", "fr": "Bilan"}, "requirements": {"en": "Requirements", "fr": "Exigences"},
    "functions": {"en": "Functions", "fr": "Fonctions"}, "interfaces": {"en": "Interfaces", "fr": "Interfaces"},
    "icd": {"en": "ICD", "fr": "ICD"}, "trace": {"en": "Traceability", "fr": "Traçabilité"},
    "decide": {"en": "Decide", "fr": "Décider"}, "analyses": {"en": "Analyses", "fr": "Analyses"},
    "vv": {"en": "V&V", "fr": "V&V"},
}
STEP_LABEL = {
    "wizard:home": {"en": "start screen", "fr": "écran d’accueil"},
    "wizard:problem": {"en": "mission wizard, problem", "fr": "assistant de mission, problème"},
    "wizard:stakeholders": {"en": "mission wizard, stakeholders", "fr": "assistant de mission, parties prenantes"},
    "wizard:alternatives": {"en": "mission wizard, alternatives", "fr": "assistant de mission, solutions de rechange"},
    "wizard:architecture": {"en": "mission wizard, architecture", "fr": "assistant de mission, architecture"},
}
# Ids that only matter to software; the readable twin is printed instead.
_HIDDEN_CONTEXT = {"study_id"}


def s(key: str, lang: str, **kw: Any) -> str:
    text = _S[key].get(lang) or _S[key]["en"]
    return text.format(**kw) if kw else text


def _label(table: dict, key: str, lang: str) -> str:
    entry = table.get(key)
    return (entry.get(lang) or entry["en"]) if entry else key


def zone(name: str | None) -> tzinfo:
    """An IANA zone name from the UI, else UTC (unknown names fall back to UTC)."""
    if not name or name == "UTC":
        return timezone.utc
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        return timezone.utc


def _zone_abbr(dt: datetime) -> str:
    if dt.tzinfo is timezone.utc:
        return "UTC"
    return dt.strftime("%Z") or dt.strftime("UTC%z")


def fmt_utc(dt: datetime | None, with_date: bool = True, tz: tzinfo = timezone.utc) -> str:
    """Date and time in ``tz`` (UTC by default), with the zone named on full stamps."""
    if dt is None:
        return ""
    dt = dt.astimezone(tz)
    return f"{dt.strftime('%Y-%m-%d %H:%M')} {_zone_abbr(dt)}" if with_date else dt.strftime("%H:%M")


WorksheetLookup = Callable[[str, str, str], tuple[str | None, str | None, int]]
"""(worksheet_id, question_id, lang) → (worksheet title, question text, question order)."""


def _ws_texts(entry: dict, lookup: WorksheetLookup | None, lang: str) -> tuple[str, str, int]:
    ws = entry.get("worksheet") or {}
    wid, q = str(ws.get("id", "")), str(ws.get("q", ""))
    title = question = None
    order = 10_000
    if lookup:
        title, question, order = lookup(wid, q, lang)
    return (title or ws.get("title") or wid, question or ws.get("q_text") or ws.get("question") or q, order)


def _context_value(k: str, v: Any, lang: str) -> str:
    sv = str(v)
    if k == "tab" and sv in TAB_LABEL:
        return _label(TAB_LABEL, sv, lang)
    if k == "step" and sv in STEP_LABEL:
        return _label(STEP_LABEL, sv, lang)
    if k == "gate":
        return sv.upper()
    if k == "level" and sv == "4":
        return "V&V"
    return sv


def _context_items(entry: dict, lang: str) -> list[tuple[str, str]]:
    ctx = entry.get("context") or {}
    items = []
    for k, v in ctx.items():
        if v is None or v == "" or v is False or k in _HIDDEN_CONTEXT:
            continue
        items.append((_label(CONTEXT_LABEL, k, lang), _context_value(k, v, lang)))
    return items


def group(entries: list[dict], tz: tzinfo = timezone.utc) -> "OrderedDict[str, OrderedDict[str, list[dict]]]":
    """day (YYYY-MM-DD in ``tz``) → tool → entries, all ascending in time."""
    epoch = datetime.min.replace(tzinfo=timezone.utc)
    ordered = sorted(entries, key=lambda e: parse_ts(e.get("ts")) or epoch)
    days: OrderedDict[str, OrderedDict[str, list[dict]]] = OrderedDict()
    for e in ordered:
        dt = parse_ts(e.get("ts"))
        day = dt.astimezone(tz).strftime("%Y-%m-%d") if dt else "—"
        days.setdefault(day, OrderedDict()).setdefault(str(e.get("tool") or "?"), []).append(e)
    return days


def _check_mark(e: dict) -> str:
    """A worksheet checkbox answer (smo-common's ``checked``) as [x] / [ ]."""
    c = (e.get("worksheet") or {}).get("checked")
    return "[x] " if c is True else "[ ] " if c is False else ""


def _meta_bits(e: dict, lang: str, tz: tzinfo = timezone.utc) -> list[str]:
    bits = []
    sim = parse_ts(e.get("sim_ts"))
    if sim:
        bits.append(s("sim", lang, t=fmt_utc(sim)))     # simulated time stays UTC
    if e.get("edited"):
        bits.append(s("edited", lang, t=fmt_utc(parse_ts(e.get("updated_ts")), with_date=False, tz=tz)))
    return bits


def tools_used(entries: list[dict], lang: str) -> list[str]:
    seen = []
    for e in sorted(entries, key=lambda e: e.get("ts") or ""):
        t = str(e.get("tool") or "")
        if t and t not in seen:
            seen.append(t)
    return [_label(TOOL_LABEL, t, lang) for t in seen]


# ─── Workbook structure ───────────────────────────────────────────────────
#
# The export reads like a completed learner workbook: worksheets in workbook
# order, parts in order, each part with its decision records (structured
# blocks) and the worksheet answers; then the decisions still open; then the
# free log, chronologically.

PartsOf = Callable[[str, str], list[tuple[str, str]]]
"""(worksheet id, lang) → [(question id, question text)] in workbook order."""


def _is_workbook_item(e: dict) -> bool:
    ws = e.get("worksheet") or {}
    if not ws.get("id"):
        return False
    if e.get("kind") == "worksheet":
        return True
    return e.get("kind") == "decision" and (ws.get("section") == "decision" or isinstance(e.get("record"), dict))


_NUM = re.compile(r"(\d+)\.(\d+)")


def worksheet_number(wid: str) -> str | None:
    m = _NUM.search(wid or "")
    return f"{m.group(1)}.{m.group(2)}" if m else None


def _wkey(wid: str) -> tuple:
    m = _NUM.search(wid or "")
    return (int(m.group(1)), int(m.group(2))) if m else (999, 999)


def workbook(entries: list[dict], lookup: WorksheetLookup | None, lang: str,
             open_decisions: list[dict] | None = None, only: str | None = None,
             parts_of: PartsOf | None = None) -> "OrderedDict[str, dict]":
    """worksheet id → {title, number, parts: part id → {text, order, decisions, answers, open}}."""
    epoch = datetime.min.replace(tzinfo=timezone.utc)
    items = sorted((e for e in entries if _is_workbook_item(e)), key=lambda e: parse_ts(e.get("ts")) or epoch)
    sheets: dict[str, dict] = {}

    def look(wid: str, qid: str) -> tuple[str | None, str | None, int]:
        if not lookup:
            return None, None, 10_000
        try:
            return lookup(wid, qid, lang)
        except Exception:  # noqa: BLE001 - a lookup that does not know the part
            return None, None, 10_000

    def sheet(wid: str, title_hint: str | None = None) -> dict:
        if wid not in sheets:
            sheets[wid] = {"title": title_hint or wid, "number": worksheet_number(wid), "parts": {},
                           "_looked": False}
            if parts_of and only:
                for i, (qid, text) in enumerate(parts_of(wid, lang)):
                    sheets[wid]["parts"][qid] = {"text": text, "order": i, "decisions": [], "answers": [], "open": []}
                    if i == 0:
                        t, _, _ = look(wid, qid)
                        if t:
                            sheets[wid]["title"], sheets[wid]["_looked"] = t, True
        return sheets[wid]

    def part(sh: dict, wid: str, qid: str, text_hint: str | None = None) -> dict:
        if qid not in sh["parts"]:
            title, text, order = look(wid, qid)
            if title and not sh["_looked"]:
                sh["title"], sh["_looked"] = title, True
            sh["parts"][qid] = {"text": text or text_hint or qid, "order": order,
                                "decisions": [], "answers": [], "open": []}
        return sh["parts"][qid]

    if only:
        sheet(only)
    for e in items:
        ws = e.get("worksheet") or {}
        wid, qid = str(ws.get("id")), str(ws.get("q") or "")
        if only and wid != only:
            continue
        sh = sheet(wid, ws.get("title"))
        p = part(sh, wid, qid, ws.get("q_text") or ws.get("question"))
        (p["decisions"] if e.get("kind") == "decision" else p["answers"]).append(e)
    for d in open_decisions or []:
        wid = d.get("worksheet")
        if not wid or (only and wid != only) or (not only and wid not in sheets):
            continue
        sh = sheet(wid, d.get("worksheet_title"))
        part(sh, wid, d.get("q") or "", d.get("part_title"))["open"].append(d)
    out: OrderedDict[str, dict] = OrderedDict()
    for wid in sorted(sheets, key=_wkey):
        sh = sheets[wid]
        sh.pop("_looked", None)
        sh["parts"] = OrderedDict(sorted(sh["parts"].items(), key=lambda kv: kv[1]["order"]))
        out[wid] = sh
    return out


def _sheet_heading(wid: str, sh: dict, lang: str) -> str:
    num = sh.get("number")
    title = sh["title"] if sh["title"] != wid else ""
    if num and wid.startswith("LW-"):
        return f"{s('worksheet', lang)} {num}" + (f" · {title}" if title else "")
    return f"{wid}" + (f" · {title}" if title else "")


def _gate_text(d: dict, lang: str) -> str:
    return s("by_gate", lang, g=str(d.get("gate") or "").upper())


# ─── Decision record helpers ──────────────────────────────────────────────

def _rec(e: dict) -> dict | None:
    r = e.get("record")
    return r if isinstance(r, dict) and r.get("decision_id") else None


def _fl(name: str, lang: str) -> str:
    from .decisions import field_label
    return field_label(name, lang)


def _seat(seat: str | None, lang: str) -> str:
    from .decisions import seat_label
    return seat_label(seat, lang)


def _record_meta(e: dict, rec: dict, lang: str, tz: tzinfo) -> str:
    bits = []
    if rec.get("seat"):
        bits.append(f"{s('owner', lang)} {_seat(rec['seat'], lang)}")
    if rec.get("gate"):
        bits.append(_gate_text(rec, lang))
    bits.append(s("recorded", lang, t=fmt_utc(parse_ts(e.get("ts")), tz=tz)))
    bits += _meta_bits(e, lang, tz)
    return " · ".join(bits)


def _opt_values(o: dict, lang: str) -> str:
    from .decisions import fmt_value
    return ", ".join(f"{k} {fmt_value(v, lang)}" for k, v in (o.get("values") or {}).items())


def _opt_score(o: dict, lang: str) -> str:
    from .decisions import fmt_value
    if "score" not in o:
        return ""
    sc = o["score"]
    if isinstance(sc, float) and 0 <= sc <= 1:
        return f"{round(sc * 100)}{NBSP}%"
    return fmt_value(sc, lang)


def _colon(lang: str) -> str:
    return f"{NBSP}:" if lang == "fr" else ":"


# ─── Markdown ─────────────────────────────────────────────────────────────

def _md_text(text: str) -> str:
    # Keep the participant's text as written; only stop a leading '#' or
    # '---' from turning into a heading or rule in the export.
    out = []
    for line in text.splitlines() or [""]:
        if line.lstrip().startswith(("#", "---", "===")):
            line = "\\" + line
        out.append(line)
    return "  \n".join(out)


def _md_cell(text: Any) -> str:
    return str(text).replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip() or " "


def md_decision(e: dict, lang: str, tz: tzinfo = timezone.utc, level: int = 5) -> list[str]:
    """One decision record as a structured Markdown block."""
    from .decisions import criterion_text, evidence_text
    rec = _rec(e)
    h = "#" * level
    if rec is None:          # a decision whose record was dropped elsewhere: its text says it all
        return [f"{h} {_label(KIND_LABEL, 'decision', lang)}", "",
                f"_{fmt_utc(parse_ts(e.get('ts')), tz=tz)}_", "", _md_text(e.get("text", "")), ""]
    c = _colon(lang)
    L = [f"{h} {_label(KIND_LABEL, 'decision', lang)} {rec['decision_id']} · {rec.get('question') or ''}".rstrip(" ·"), ""]
    L.append(f"_{_record_meta(e, rec, lang, tz)}_")
    L.append("")
    if rec.get("subject"):
        L += [f"**{s('subject', lang)}{c}** {_md_text(rec['subject'])}", ""]
    if rec.get("choice"):
        L += [f"**{_fl('choice', lang)}{c}** {_md_text(rec['choice'])}", ""]
    if rec.get("options"):
        L.append(f"**{_fl('options', lang)}**")
        L.append("")
        L.append(f"| {s('option', lang)} | {s('values', lang)} | {s('score', lang)} | |")
        L.append("|---|---|---:|---|")
        for o in rec["options"]:
            name = _md_cell(o["name"]) + (f" — {_md_cell(o['summary'])}" if o.get("summary") else "")
            if o.get("chosen"):
                name = f"**{name}**"
            L.append(f"| {name} | {_md_cell(_opt_values(o, lang))} | {_opt_score(o, lang) or ' '} | "
                     f"{s('chosen', lang) if o.get('chosen') else ' '} |")
        L.append("")
    if rec.get("criteria"):
        L += [f"**{_fl('criteria', lang)}{c}** " + "; ".join(criterion_text(x, lang) for x in rec["criteria"]), ""]
    if rec.get("rationale"):
        L += [f"**{_fl('rationale', lang)}{c}** {_md_text(rec['rationale'])}", ""]
    if rec.get("evidence"):
        L.append(f"**{_fl('evidence', lang)}**")
        L.append("")
        L += [f"- {evidence_text(x, lang)}" for x in rec["evidence"]]
        L.append("")
    for k in ("consequences", "margin_impact", "open_issues"):
        if rec.get(k):
            L += [f"**{_fl(k, lang)}{c}** {_md_text(rec[k])}", ""]
    return L


def _md_answer(a: dict, lang: str, tz: tzinfo) -> list[str]:
    meta = _meta_bits(a, lang, tz)
    stamp = fmt_utc(parse_ts(a.get("ts")), tz=tz)
    return [f"_{stamp}{' · ' + '; '.join(meta) if meta else ''}_  ", _check_mark(a) + _md_text(a.get("text", "")), ""]


def _md_open(d: dict, lang: str) -> str:
    return (f"- [ ] **{d['id']}** {d['question']} — {s('owner', lang)} {d.get('seat_label') or d.get('seat')}"
            f" · {_gate_text(d, lang)}")


def md_workbook(book: "OrderedDict[str, dict]", lang: str, tz: tzinfo, base: int = 2) -> list[str]:
    h = "#" * base
    L: list[str] = []
    for wid, sh in book.items():
        L += [f"{h} {_sheet_heading(wid, sh, lang)}", ""]
        for qid, p in sh["parts"].items():
            if not (p["decisions"] or p["answers"] or p["open"]):
                continue
            L += [f"{h}# {p['text']}", ""]
            for e in p["decisions"]:
                L += md_decision(e, lang, tz, level=base + 2)
            if p["answers"]:
                if p["decisions"]:
                    L += [f"**{s('answers', lang)}**", ""]
                for a in p["answers"]:
                    L += _md_answer(a, lang, tz)
            if p["open"]:
                L += [f"_{s('open_here', lang)}_", ""]
                L += [_md_open(d, lang) for d in p["open"]]
                L.append("")
    return L


def _md_log(entries: list[dict], lang: str, tz: tzinfo, base: int = 2) -> list[str]:
    h = "#" * base
    L: list[str] = []
    for day, tools in group(entries, tz).items():
        L += [f"{h}# {day}", ""]
        for tool, items in tools.items():
            L += [f"{h}## {_label(TOOL_LABEL, tool, lang)}", ""]
            for e in items:
                if e.get("kind") == "worksheet":      # an answer outside the workbook (no id)
                    title, question, _ = _ws_texts(e, None, lang)
                    L += [f"**{question}**", ""] + _md_answer(e, lang, tz)
                    continue
                head = f"**{fmt_utc(parse_ts(e.get('ts')), with_date=False, tz=tz)} · {_label(KIND_LABEL, str(e.get('kind')), lang)}**"
                meta = _meta_bits(e, lang, tz)
                if meta:
                    head += f" _({'; '.join(meta)})_"
                L += [head, "", _md_text(e.get("text", ""))]
                ctx = _context_items(e, lang)
                if ctx:
                    L += ["", f"_{s('context', lang)}{_colon(lang)} " + " · ".join(f"{k} {v}" for k, v in ctx) + "_"]
                L.append("")
    return L


def _split_entries(entries: list[dict]) -> tuple[list[dict], list[dict]]:
    book = [e for e in entries if _is_workbook_item(e)]
    log = [e for e in entries if not _is_workbook_item(e)]
    return book, log


def _open_by_gate(open_decisions: list[dict] | None, gates: list[dict] | None) -> "OrderedDict[str, list[dict]]":
    out: OrderedDict[str, list[dict]] = OrderedDict()
    order = [g["id"] for g in gates or []]
    for g in order:
        out[g] = []
    for d in open_decisions or []:
        out.setdefault(d.get("gate") or "?", []).append(d)
    return OrderedDict((k, v) for k, v in out.items() if v)


def render_markdown(*, entries: list[dict], person_label: str, exported_at: datetime,
                    expires_at: datetime | None, retention_h: float, lang: str,
                    lookup: WorksheetLookup | None = None, tz: tzinfo = timezone.utc,
                    decisions: dict | None = None, worksheet: str | None = None,
                    parts_of: PartsOf | None = None) -> str:
    """The logbook as a completed workbook (``decisions`` = decisions.localised(); optional).

    ``worksheet``: only that worksheet ("Download this worksheet", "Copy as
    Markdown"), every part listed, with its open decisions.
    """
    open_d = [d for d in (decisions or {}).get("decisions", []) if d.get("status") == "open"]
    book_entries, log_entries = _split_entries(entries)
    if worksheet:
        book_entries = [e for e in book_entries if (e.get("worksheet") or {}).get("id") == worksheet]
        book = workbook(book_entries, lookup, lang, open_d, only=worksheet, parts_of=parts_of)
        sh = book.get(worksheet) or {"title": worksheet, "number": worksheet_number(worksheet), "parts": {}}
        L = [f"# {_sheet_heading(worksheet, sh, lang)}", "",
             f"| | |\n|---|---|",
             f"| **{s('person', lang)}** | {person_label} |",
             f"| **{s('exported', lang)}** | {fmt_utc(exported_at, tz=tz)} |",
             f"| **{s('entries', lang)}** | {len(book_entries)} |", ""]
        body = md_workbook(book, lang, tz, base=2)
        # md_workbook repeats the worksheet heading at level 2: drop it, the title says it.
        if body and body[0].startswith("## "):
            body = body[2:]
        L += body if any(x.strip() for x in body) else [s("none", lang), ""]
        return "\n".join(L).rstrip() + "\n"

    L = [f"# {s('title', lang)}", "",
         f"| | |\n|---|---|",
         f"| **{s('person', lang)}** | {person_label} |",
         f"| **{s('exported', lang)}** | {fmt_utc(exported_at, tz=tz)} |",
         f"| **{s('tools', lang)}** | {', '.join(tools_used(entries, lang)) or '—'} |",
         f"| **{s('entries', lang)}** | {len(entries)} |"]
    n_dec = sum(1 for e in book_entries if e.get("kind") == "decision")
    if n_dec or open_d:
        L.append(f"| **{s('decisions', lang)}** | {s('decisions_count', lang, n=n_dec, o=len(open_d))} |")
    if tz is not timezone.utc:
        L.append(f"| **{s('tz', lang)}** | {getattr(tz, 'key', str(tz))} |")
    L += ["", f"*{s('private', lang)}*", ""]
    if not entries:
        L += [s("none", lang), ""]
    if book_entries:
        L += [f"## {s('workbook', lang)}", ""]
        L += md_workbook(workbook(book_entries, lookup, lang, open_d), lang, tz, base=3)
    has_design = any(e.get("tool") == "design" for e in entries)
    by_gate = _open_by_gate(open_d, (decisions or {}).get("gates")) if has_design else {}
    if by_gate:
        L += [f"## {s('open_decisions', lang)}", "", s("open_help", lang), ""]
        labels = {g["id"]: g["label"] for g in (decisions or {}).get("gates", [])}
        for g, items in by_gate.items():
            L += [f"### {labels.get(g, g.upper())}", ""]
            for d in items:
                where = f"{s('worksheet', lang)} {worksheet_number(d.get('worksheet') or '')}" + (
                    f", {d['part_title']}" if d.get("part_title") else "")
                L.append(_md_open(d, lang) + f" · {where}")
            L.append("")
    if log_entries:
        L += [f"## {s('log', lang)}", ""]
        L += _md_log(log_entries, lang, tz, base=2)
    L += ["---", ""]
    if expires_at:
        L.append(s("footer", lang, t=fmt_utc(expires_at, tz=tz), h=f"{retention_h:g}"))
    else:
        L.append(s("footer_none", lang))
    L.append("")
    return "\n".join(L)


# ─── HTML (print-ready) ───────────────────────────────────────────────────

PRINT_CSS = """
@page { size: auto; margin: 16mm 15mm 18mm; }
:root { --ink: #141619; --ink-2: #383C42; --ink-3: #4A4F56; --rule: #D5D9DE; --brand: #8F001A; }
* { box-sizing: border-box; }
html { background: #fff; }
body { margin: 0 auto; max-width: 180mm; padding: 12mm 0; color: var(--ink);
       font: 10.5pt/1.45 'IBM Plex Sans', 'Segoe UI', system-ui, -apple-system, Arial, sans-serif; }
h1 { margin: 0 0 4mm; font-size: 18pt; font-weight: 600; letter-spacing: .005em;
     padding-bottom: 2mm; border-bottom: 2px solid var(--brand); }
h2 { margin: 9mm 0 2mm; font-size: 14pt; font-weight: 600; padding-bottom: 1mm; border-bottom: 1px solid var(--ink-2); }
h3 { margin: 6mm 0 2mm; font-size: 12pt; font-weight: 600; padding-bottom: .6mm; border-bottom: 1px solid var(--rule); }
h4 { margin: 4mm 0 1.5mm; font-size: 10.5pt; font-weight: 600; color: var(--ink-2); }
h5 { margin: 3mm 0 1mm; font-size: 10.5pt; font-weight: 600; }
h3.day { font-family: 'IBM Plex Mono', Menlo, Consolas, monospace; font-variant-numeric: tabular-nums; }
table.meta { border-collapse: collapse; margin: 0 0 3mm; font-size: 10pt; }
table.meta th { text-align: left; font-weight: 500; color: var(--ink-3); padding: .6mm 6mm .6mm 0; vertical-align: top; }
table.meta td { padding: .6mm 0; }
.private { margin: 0 0 4mm; font-size: 9pt; color: var(--ink-3); }
.entry { break-inside: avoid; page-break-inside: avoid; margin: 0 0 3mm; padding-left: 3mm; border-left: 2px solid var(--rule); }
.entry.decision { border-left-color: var(--ink-2); }
.stamp { font-family: 'IBM Plex Mono', Menlo, Consolas, monospace; font-variant-numeric: tabular-nums; font-size: 9pt; color: var(--ink-3); }
.kind { font-size: 9pt; font-weight: 600; text-transform: uppercase; letter-spacing: .04em; color: var(--ink-2); margin-left: 2mm; }
.meta-bits { font-size: 9pt; color: var(--ink-3); margin-left: 2mm; }
.text { white-space: pre-wrap; overflow-wrap: anywhere; margin: .8mm 0 0; }
.ctx { margin: .8mm 0 0; font-size: 9pt; color: var(--ink-3); }
.ctx span + span::before { content: " · "; }
.dr { break-inside: avoid; page-break-inside: avoid; margin: 2mm 0 4mm; padding: 2mm 0 1mm 3mm; border-left: 2px solid var(--ink-2); }
.dr h5 { margin: 0 0 .5mm; }
.dr .id { font-family: 'IBM Plex Mono', Menlo, Consolas, monospace; font-weight: 500; color: var(--ink-3); margin-right: 1.5mm; }
.dr .meta { margin: 0 0 1.5mm; font-size: 9pt; color: var(--ink-3); }
.dr dl { display: grid; grid-template-columns: 34mm 1fr; gap: 1mm 3mm; margin: 0; }
.dr dt { font-size: 9pt; font-weight: 600; color: var(--ink-2); }
.dr dd { margin: 0; white-space: pre-wrap; overflow-wrap: anywhere; }
.dr dd ul { margin: 0; padding-left: 4mm; white-space: normal; }
.dr dt.wide, .dr dd.wide { grid-column: 1 / -1; }
table.opts td.num, table.opts td:last-child, table.opts th { white-space: nowrap; }
table.opts { border-collapse: collapse; width: 100%; font-size: 9.5pt; white-space: normal; }
table.opts th, table.opts td { text-align: left; padding: .6mm 2mm .6mm 0; border-bottom: 1px solid var(--rule); vertical-align: top; }
table.opts th { font-weight: 500; color: var(--ink-3); }
table.opts td.num { text-align: right; font-variant-numeric: tabular-nums; }
table.opts tr.chosen td { font-weight: 600; }
.answer { margin: 1mm 0 2.5mm; }
.open { margin: 1mm 0 3mm; padding: 0; list-style: none; font-size: 9.5pt; color: var(--ink-2); }
.open li { margin: .6mm 0; }
.open li::before { content: "☐ "; }
.open .id { font-family: 'IBM Plex Mono', Menlo, Consolas, monospace; }
.label { font-size: 9pt; font-weight: 600; color: var(--ink-3); margin: 2mm 0 .5mm; }
footer { margin-top: 10mm; padding-top: 2mm; border-top: 1px solid var(--rule); font-size: 9pt; color: var(--ink-3); }
@media screen { body { padding: 12mm 16px; } }
@media print { body { padding: 0; max-width: none; } a { color: inherit; text-decoration: none; } }
"""


def _h(text: Any) -> str:
    return html.escape(str(text), quote=True)


def html_decision(e: dict, lang: str, tz: tzinfo = timezone.utc) -> str:
    from .decisions import criterion_text, evidence_text
    rec = _rec(e)
    if rec is None:
        return (f'<div class="entry decision"><span class="stamp">{_h(fmt_utc(parse_ts(e.get("ts")), tz=tz))}</span>'
                f'<span class="kind">{_h(_label(KIND_LABEL, "decision", lang))}</span>'
                f'<p class="text">{_h(e.get("text", ""))}</p></div>')
    P = ['<section class="dr">',
         f'<h5><span class="id">{_h(rec["decision_id"])}</span>{_h(rec.get("question") or "")}</h5>',
         f'<p class="meta">{_h(_record_meta(e, rec, lang, tz))}</p>', "<dl>"]

    def row(label: str, body: str) -> None:
        P.append(f"<dt>{_h(label)}</dt><dd>{body}</dd>")

    if rec.get("subject"):
        row(s("subject", lang), _h(rec["subject"]))
    if rec.get("choice"):
        row(_fl("choice", lang), f"<strong>{_h(rec['choice'])}</strong>")
    if rec.get("options"):
        rows = "".join(
            f'<tr{" class=chosen" if o.get("chosen") else ""}><td>{_h(o["name"])}'
            + (f'<br><span class="stamp">{_h(o["summary"])}</span>' if o.get("summary") else "")
            + f'</td><td>{_h(_opt_values(o, lang))}</td><td class="num">{_h(_opt_score(o, lang))}</td>'
            f'<td>{_h(s("chosen", lang)) if o.get("chosen") else ""}</td></tr>'
            for o in rec["options"])
        P.append(f'<dt class="wide">{_h(_fl("options", lang))}</dt><dd class="wide">'
                 f'<table class="opts"><thead><tr><th>{_h(s("option", lang))}</th><th>{_h(s("values", lang))}</th>'
            f'<th>{_h(s("score", lang))}</th><th></th></tr></thead><tbody>{rows}</tbody></table></dd>')
    if rec.get("criteria"):
        row(_fl("criteria", lang), _h("; ".join(criterion_text(x, lang) for x in rec["criteria"])))
    if rec.get("rationale"):
        row(_fl("rationale", lang), _h(rec["rationale"]))
    if rec.get("evidence"):
        row(_fl("evidence", lang), "<ul>" + "".join(f"<li>{_h(evidence_text(x, lang))}</li>" for x in rec["evidence"]) + "</ul>")
    for k in ("consequences", "margin_impact", "open_issues"):
        if rec.get(k):
            row(_fl(k, lang), _h(rec[k]))
    P.append("</dl></section>")
    return "\n".join(P)


def _html_answer(a: dict, lang: str, tz: tzinfo) -> str:
    meta = _meta_bits(a, lang, tz)
    return ('<div class="entry worksheet answer">'
            f'<span class="stamp">{_h(fmt_utc(parse_ts(a.get("ts")), tz=tz))}</span>'
            + (f'<span class="meta-bits">{_h("; ".join(meta))}</span>' if meta else "")
            + f'<p class="text">{_h(_check_mark(a) + a.get("text", ""))}</p></div>')


def _html_open(d: dict, lang: str, where: bool = False) -> str:
    extra = ""
    if where:
        extra = f" · {s('worksheet', lang)} {worksheet_number(d.get('worksheet') or '')}" + (
            f", {d['part_title']}" if d.get("part_title") else "")
    return (f'<li><span class="id">{_h(d["id"])}</span> {_h(d["question"])} — '
            f'{_h(s("owner", lang))} {_h(d.get("seat_label") or d.get("seat"))} · {_h(_gate_text(d, lang))}{_h(extra)}</li>')


def html_workbook(book: "OrderedDict[str, dict]", lang: str, tz: tzinfo, top: int = 2) -> list[str]:
    P: list[str] = []
    for wid, sh in book.items():
        P.append(f"<section><h{top}>{_h(_sheet_heading(wid, sh, lang))}</h{top}>")
        for qid, p in sh["parts"].items():
            if not (p["decisions"] or p["answers"] or p["open"]):
                continue
            P.append(f"<h{top + 1}>{_h(p['text'])}</h{top + 1}>")
            P += [html_decision(e, lang, tz) for e in p["decisions"]]
            if p["answers"]:
                if p["decisions"]:
                    P.append(f'<p class="label">{_h(s("answers", lang))}</p>')
                P += [_html_answer(a, lang, tz) for a in p["answers"]]
            if p["open"]:
                P.append(f'<p class="label">{_h(s("open_here", lang))}</p><ul class="open">'
                         + "".join(_html_open(d, lang) for d in p["open"]) + "</ul>")
        P.append("</section>")
    return P


def _html_head(title: str, lang: str) -> list[str]:
    return [f'<!doctype html>\n<html lang="{_h(lang)}">\n<head>\n<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{_h(title)}</title>",
            f"<style>{PRINT_CSS}</style>\n</head>\n<body>"]


def render_html(*, entries: list[dict], person_label: str, exported_at: datetime,
                expires_at: datetime | None, retention_h: float, lang: str,
                lookup: WorksheetLookup | None = None, tz: tzinfo = timezone.utc,
                decisions: dict | None = None, worksheet: str | None = None,
                parts_of: PartsOf | None = None) -> str:
    open_d = [d for d in (decisions or {}).get("decisions", []) if d.get("status") == "open"]
    book_entries, log_entries = _split_entries(entries)
    meta_rows = [(s("person", lang), person_label), (s("exported", lang), fmt_utc(exported_at, tz=tz))]
    if worksheet:
        book_entries = [e for e in book_entries if (e.get("worksheet") or {}).get("id") == worksheet]
        book = workbook(book_entries, lookup, lang, open_d, only=worksheet, parts_of=parts_of)
        sh = book.get(worksheet) or {"title": worksheet, "number": worksheet_number(worksheet), "parts": {}}
        title = _sheet_heading(worksheet, sh, lang)
        P = _html_head(f"{title} — {person_label}", lang)
        P.append(f"<h1>{_h(title)}</h1>")
        P.append('<table class="meta">' + "".join(f"<tr><th>{_h(k)}</th><td>{_h(v)}</td></tr>" for k, v in meta_rows)
                 + f"<tr><th>{_h(s('entries', lang))}</th><td>{len(book_entries)}</td></tr></table>")
        body = html_workbook(book, lang, tz, top=2)
        # drop the repeated worksheet heading
        P += [b.replace(f"<section><h2>{_h(title)}</h2>", "<section>", 1) for b in body]
        P.append("</body>\n</html>\n")
        return "\n".join(P)

    title = s("title", lang)
    P = _html_head(f"{title} — {person_label} — {exported_at.strftime('%Y-%m-%d')}", lang)
    P.append(f"<h1>{_h(title)}</h1>")
    rows = meta_rows + [(s("tools", lang), ", ".join(tools_used(entries, lang)) or "—"),
                        (s("entries", lang), str(len(entries)))]
    n_dec = sum(1 for e in book_entries if e.get("kind") == "decision")
    if n_dec or open_d:
        rows.append((s("decisions", lang), s("decisions_count", lang, n=n_dec, o=len(open_d))))
    if tz is not timezone.utc:
        rows.append((s("tz", lang), getattr(tz, "key", str(tz))))
    P.append('<table class="meta">' + "".join(f"<tr><th>{_h(k)}</th><td>{_h(v)}</td></tr>" for k, v in rows) + "</table>")
    P.append(f'<p class="private">{_h(s("private", lang))}</p>')
    if not entries:
        P.append(f"<p>{_h(s('none', lang))}</p>")
    if book_entries:
        P.append(f"<h2>{_h(s('workbook', lang))}</h2>")
        P += html_workbook(workbook(book_entries, lookup, lang, open_d), lang, tz, top=3)
    has_design = any(e.get("tool") == "design" for e in entries)
    by_gate = _open_by_gate(open_d, (decisions or {}).get("gates")) if has_design else {}
    if by_gate:
        labels = {g["id"]: g["label"] for g in (decisions or {}).get("gates", [])}
        P.append(f"<section><h2>{_h(s('open_decisions', lang))}</h2><p class=\"private\">{_h(s('open_help', lang))}</p>")
        for g, items in by_gate.items():
            P.append(f"<h3>{_h(labels.get(g, g.upper()))}</h3><ul class=\"open\">"
                     + "".join(_html_open(d, lang, where=True) for d in items) + "</ul>")
        P.append("</section>")
    if log_entries:
        P.append(f"<h2>{_h(s('log', lang))}</h2>")
        for day, tools in group(log_entries, tz).items():
            P.append(f'<section><h3 class="day">{_h(day)}</h3>')
            for tool, items in tools.items():
                P.append(f"<h4>{_h(_label(TOOL_LABEL, tool, lang))}</h4>")
                for e in items:
                    kind = str(e.get("kind"))
                    if kind == "worksheet":
                        _, question, _ = _ws_texts(e, None, lang)
                        P.append(f'<p class="label">{_h(question)}</p>' + _html_answer(e, lang, tz))
                        continue
                    meta = _meta_bits(e, lang, tz)
                    P.append(f'<div class="entry {_h(kind)}">'
                             f'<span class="stamp">{_h(fmt_utc(parse_ts(e.get("ts")), with_date=False, tz=tz))}</span>'
                             f'<span class="kind">{_h(_label(KIND_LABEL, kind, lang))}</span>'
                             + (f'<span class="meta-bits">{_h("; ".join(meta))}</span>' if meta else "")
                             + f'<p class="text">{_h(e.get("text", ""))}</p>')
                    ctx = _context_items(e, lang)
                    if ctx:
                        P.append('<p class="ctx">' + "".join(f"<span>{_h(k)} {_h(v)}</span>" for k, v in ctx) + "</p>")
                    P.append("</div>")
            P.append("</section>")
    footer = (s("footer", lang, t=fmt_utc(expires_at, tz=tz), h=f"{retention_h:g}") if expires_at
              else s("footer_none", lang))
    P.append(f"<footer>{_h(footer)}</footer>\n</body>\n</html>\n")
    return "\n".join(P)


# ─── JSON ─────────────────────────────────────────────────────────────────

def render_json(*, entries: list[dict], person_label: str, exported_at: datetime,
                expires_at: datetime | None, retention_h: float, lang: str,
                lookup: WorksheetLookup | None = None, tz: tzinfo = timezone.utc,
                decisions: dict | None = None, worksheet: str | None = None,
                parts_of: PartsOf | None = None) -> str:
    from .store import iso
    epoch = datetime.min.replace(tzinfo=timezone.utc)
    if worksheet:
        entries = [e for e in entries if (e.get("worksheet") or {}).get("id") == worksheet]
    ordered = sorted(entries, key=lambda e: parse_ts(e.get("ts")) or epoch)
    out = []
    for e in ordered:
        e = dict(e)
        if e.get("kind") == "worksheet":
            title, question, _ = _ws_texts(e, lookup, lang)
            e["worksheet"] = {**(e.get("worksheet") or {}), "title": title, "q_text": question}
        out.append(e)
    doc = {
        "v": 1,
        "person": person_label,
        "exported_at": iso(exported_at),
        "expires_at": iso(expires_at) if expires_at else None,
        "retention_h": retention_h,
        "lang": lang,
        "count": len(out),
        "entries": out,
    }
    if decisions:
        doc["open_decisions"] = [{k: d.get(k) for k in ("id", "part", "question", "seat", "gate")}
                                 for d in decisions.get("decisions", []) if d.get("status") == "open"
                                 and (not worksheet or d.get("worksheet") == worksheet)]
    if worksheet:
        doc["worksheet"] = worksheet
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


RENDERERS = {
    "md": (render_markdown, "text/markdown; charset=utf-8"),
    "html": (render_html, "text/html; charset=utf-8"),
    "json": (render_json, "application/json; charset=utf-8"),
}
