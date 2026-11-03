"""Logbook export: Markdown, print-ready HTML and JSON (LOGBOOK_SPEC.md §3).

Grouped by session day (UTC), then tool, then time. Worksheet answers are
grouped under their worksheet with the question text. Both document formats
carry a header (person, export time UTC, tools used, entry count) and the
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


def _split(items: list[dict], lookup: WorksheetLookup | None, lang: str):
    """Plain entries, and worksheet answers grouped worksheet → question."""
    plain = [e for e in items if e.get("kind") != "worksheet"]
    sheets: OrderedDict[str, dict] = OrderedDict()
    for e in items:
        if e.get("kind") != "worksheet":
            continue
        title, question, order = _ws_texts(e, lookup, lang)
        wid = str((e.get("worksheet") or {}).get("id", ""))
        sheet = sheets.setdefault(wid, {"title": title, "questions": OrderedDict()})
        q = str((e.get("worksheet") or {}).get("q", ""))
        sheet["questions"].setdefault(q, {"text": question, "order": order, "answers": []})["answers"].append(e)
    for sheet in sheets.values():
        sheet["questions"] = OrderedDict(sorted(sheet["questions"].items(), key=lambda kv: kv[1]["order"]))
    return plain, sheets


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


def render_markdown(*, entries: list[dict], person_label: str, exported_at: datetime,
                    expires_at: datetime | None, retention_h: float, lang: str,
                    lookup: WorksheetLookup | None = None, tz: tzinfo = timezone.utc) -> str:
    L = []
    L.append(f"# {s('title', lang)}")
    L.append("")
    L.append(f"| | |\n|---|---|")
    L.append(f"| **{s('person', lang)}** | {person_label} |")
    L.append(f"| **{s('exported', lang)}** | {fmt_utc(exported_at, tz=tz)} |")
    L.append(f"| **{s('tools', lang)}** | {', '.join(tools_used(entries, lang)) or '—'} |")
    L.append(f"| **{s('entries', lang)}** | {len(entries)} |")
    if tz is not timezone.utc:
        L.append(f"| **{s('tz', lang)}** | {getattr(tz, 'key', str(tz))} |")
    L.append("")
    L.append(f"*{s('private', lang)}*")
    L.append("")
    if not entries:
        L.append(s("none", lang))
        L.append("")
    for day, tools in group(entries, tz).items():
        L.append(f"## {day}")
        L.append("")
        for tool, items in tools.items():
            L.append(f"### {_label(TOOL_LABEL, tool, lang)}")
            L.append("")
            plain, sheets = _split(items, lookup, lang)
            for e in plain:
                head = f"**{fmt_utc(parse_ts(e.get('ts')), with_date=False, tz=tz)} · {_label(KIND_LABEL, str(e.get('kind')), lang)}**"
                meta = _meta_bits(e, lang, tz)
                if meta:
                    head += f" _({'; '.join(meta)})_"
                L.append(head)
                L.append("")
                L.append(_md_text(e.get("text", "")))
                ctx = _context_items(e, lang)
                if ctx:
                    L.append("")
                    L.append(f"_{s('context', lang)}{NBSP if lang == 'fr' else ''}: "
                             + " · ".join(f"{k} {v}" for k, v in ctx) + "_")
                L.append("")
            for wid, sheet in sheets.items():
                L.append(f"#### {s('worksheets', lang)} — {wid} {sheet['title'] if sheet['title'] != wid else ''}".rstrip())
                L.append("")
                for q in sheet["questions"].values():
                    L.append(f"**{q['text']}**")
                    L.append("")
                    for a in q["answers"]:
                        meta = _meta_bits(a, lang, tz)
                        stamp = fmt_utc(parse_ts(a.get("ts")), with_date=False, tz=tz)
                        L.append(f"_{stamp}{' · ' + '; '.join(meta) if meta else ''}_  ")
                        L.append(_check_mark(a) + _md_text(a.get("text", "")))
                        L.append("")
    L.append("---")
    L.append("")
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
h2 { margin: 8mm 0 2mm; font-size: 13pt; font-weight: 600; padding-bottom: 1mm; border-bottom: 1px solid var(--rule);
     font-family: 'IBM Plex Mono', Menlo, Consolas, monospace; font-variant-numeric: tabular-nums; }
h3 { margin: 5mm 0 2mm; font-size: 11pt; font-weight: 600; color: var(--ink-2); text-transform: none; }
h4 { margin: 4mm 0 1.5mm; font-size: 10.5pt; font-weight: 600; }
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
.ws { margin: 2mm 0 4mm; }
.ws .q { margin: 2.5mm 0 1mm; font-weight: 600; break-after: avoid; page-break-after: avoid; }
footer { margin-top: 10mm; padding-top: 2mm; border-top: 1px solid var(--rule); font-size: 9pt; color: var(--ink-3); }
@media screen { body { padding: 12mm 16px; } }
@media print { body { padding: 0; max-width: none; } a { color: inherit; text-decoration: none; } }
"""


def _h(text: Any) -> str:
    return html.escape(str(text), quote=True)


def render_html(*, entries: list[dict], person_label: str, exported_at: datetime,
                expires_at: datetime | None, retention_h: float, lang: str,
                lookup: WorksheetLookup | None = None, tz: tzinfo = timezone.utc) -> str:
    title = s("title", lang)
    P = [f'<!doctype html>\n<html lang="{_h(lang)}">\n<head>\n<meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width, initial-scale=1">',
         f"<title>{_h(title)} — {_h(person_label)} — {_h(exported_at.strftime('%Y-%m-%d'))}</title>",
         f"<style>{PRINT_CSS}</style>\n</head>\n<body>",
         f"<h1>{_h(title)}</h1>",
         '<table class="meta">',
         f"<tr><th>{_h(s('person', lang))}</th><td>{_h(person_label)}</td></tr>",
         f"<tr><th>{_h(s('exported', lang))}</th><td>{_h(fmt_utc(exported_at, tz=tz))}</td></tr>",
         f"<tr><th>{_h(s('tools', lang))}</th><td>{_h(', '.join(tools_used(entries, lang)) or '—')}</td></tr>",
         f"<tr><th>{_h(s('entries', lang))}</th><td>{len(entries)}</td></tr>",
         (f"<tr><th>{_h(s('tz', lang))}</th><td>{_h(getattr(tz, 'key', str(tz)))}</td></tr>"
          if tz is not timezone.utc else ""),
         "</table>",
         f'<p class="private">{_h(s("private", lang))}</p>']
    if not entries:
        P.append(f"<p>{_h(s('none', lang))}</p>")
    for day, tools in group(entries, tz).items():
        P.append(f"<section><h2>{_h(day)}</h2>")
        for tool, items in tools.items():
            P.append(f"<h3>{_h(_label(TOOL_LABEL, tool, lang))}</h3>")
            plain, sheets = _split(items, lookup, lang)
            for e in plain:
                kind = str(e.get("kind"))
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
            for wid, sheet in sheets.items():
                head = wid if sheet["title"] == wid else f"{wid} · {sheet['title']}"
                P.append(f'<div class="ws"><h4>{_h(s("worksheets", lang))} — {_h(head)}</h4>')
                for q in sheet["questions"].values():
                    P.append(f'<p class="q">{_h(q["text"])}</p>')
                    for a in q["answers"]:
                        meta = _meta_bits(a, lang, tz)
                        P.append('<div class="entry worksheet">'
                                 f'<span class="stamp">{_h(fmt_utc(parse_ts(a.get("ts")), with_date=False, tz=tz))}</span>'
                                 + (f'<span class="meta-bits">{_h("; ".join(meta))}</span>' if meta else "")
                                 + f'<p class="text">{_h(_check_mark(a) + a.get("text", ""))}</p></div>')
                P.append("</div>")
        P.append("</section>")
    footer = (s("footer", lang, t=fmt_utc(expires_at, tz=tz), h=f"{retention_h:g}") if expires_at
              else s("footer_none", lang))
    P.append(f"<footer>{_h(footer)}</footer>\n</body>\n</html>\n")
    return "\n".join(P)


# ─── JSON ─────────────────────────────────────────────────────────────────

def render_json(*, entries: list[dict], person_label: str, exported_at: datetime,
                expires_at: datetime | None, retention_h: float, lang: str,
                lookup: WorksheetLookup | None = None, tz: tzinfo = timezone.utc) -> str:
    from .store import iso
    epoch = datetime.min.replace(tzinfo=timezone.utc)
    ordered = sorted(entries, key=lambda e: parse_ts(e.get("ts")) or epoch)
    out = []
    for e in ordered:
        e = dict(e)
        if e.get("kind") == "worksheet":
            title, question, _ = _ws_texts(e, lookup, lang)
            e["worksheet"] = {**(e.get("worksheet") or {}), "title": title, "q_text": question}
        out.append(e)
    return json.dumps({
        "v": 1,
        "person": person_label,
        "exported_at": iso(exported_at),
        "expires_at": iso(expires_at) if expires_at else None,
        "retention_h": retention_h,
        "lang": lang,
        "count": len(out),
        "entries": out,
    }, ensure_ascii=False, indent=2) + "\n"


RENDERERS = {
    "md": (render_markdown, "text/markdown; charset=utf-8"),
    "html": (render_html, "text/html; charset=utf-8"),
    "json": (render_json, "application/json; charset=utf-8"),
}
