"""Logbook exports: Markdown, print-ready HTML and JSON (LOGBOOK_SPEC §3).

Grouped by session day (UTC), then tool, then time. Worksheet answers are
grouped under their worksheet with the question text. Both document formats
carry a header (person label, export time UTC, tools used, entry count) and
a footer with the server deletion time. The HTML is self-contained (no
script, no external asset) and prints cleanly to A4 or Letter, so the
browser's "Save as PDF" makes the PDF.
"""
from __future__ import annotations

import html
import json
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Callable

from .store import iso, parse_ts

__all__ = ["export_filename", "to_html", "to_json", "to_markdown", "LABELS"]

#: Every label an export prints, EN and FR.
LABELS = {
    "en": {
        "title": "C2O logbook", "person": "Person", "exported": "Exported (UTC)",
        "tools": "Tools", "entries": "Entries", "deleted": "Deleted from the C2O server on {when}",
        "not_scheduled": "Nothing is stored on the C2O server for this logbook.",
        "private": "Private to you. Hand this file in if it is to be graded.",
        "sim": "sim time", "edited": "edited", "worksheets": "Worksheets",
        "this_browser": "this browser", "empty": "No entries.", "context": "Context",
        "kind": {"decision": "Decision", "thought": "Thought", "reflection": "Reflection",
                 "observation": "Observation", "worksheet": "Worksheet answer"},
        "tool": {"mcs": "Mission control", "delayed_tm": "Delayed TM", "orbit": "Orbit tools",
                 "radio": "Radio view", "docs": "Documentation", "instructor": "Instructor",
                 "design": "SpaceCDF", "portal": "Welcome page"},
        "ctx": {"page": "page", "procedure": "procedure", "step": "step", "alarm_id": "alarm",
                "param": "parameter", "study_id": "study", "position": "position",
                "scenario": "scenario", "sim_status": "sim state", "report": "report", "dump": "dump",
                "station": "station", "pass": "pass", "doc": "document", "phase": "phase",
                "anomaly": "anomaly", "command": "command", "gonogo": "GO/NO-GO",
                "gate": "gate", "proposal": "proposal",
                "study_name": "study", "tab": "tab", "level": "level",
                "element": "element", "decision": "on"},
        "done": "done", "not_done": "not done",
    },
    "fr": {
        "title": "Journal de bord C2O", "person": "Personne", "exported": "Exporté (UTC)",
        "tools": "Outils", "entries": "Entrées",
        "deleted": "Supprimé du serveur C2O le {when}",
        "not_scheduled": "Rien n’est conservé sur le serveur C2O pour ce journal.",
        "private": "Privé. Remettez ce fichier s’il doit être évalué.",
        "sim": "heure sim", "edited": "modifiée", "worksheets": "Fiches",
        "this_browser": "ce navigateur", "empty": "Aucune entrée.", "context": "Contexte",
        "kind": {"decision": "Décision", "thought": "Pensée",
                 "reflection": "Réflexion", "observation": "Observation",
                 "worksheet": "Réponse de fiche"},
        "tool": {"mcs": "Contrôle de mission", "delayed_tm": "TM différée",
                 "orbit": "Outils d’orbite", "radio": "Vue radio", "docs": "Documentation",
                 "instructor": "Instructeur", "design": "SpaceCDF", "portal": "Page d’accueil"},
        "ctx": {"page": "page", "procedure": "procédure", "step": "étape", "alarm_id": "alarme",
                "param": "paramètre", "study_id": "étude", "position": "poste",
                "scenario": "scénario", "sim_status": "état de la sim", "report": "rapport", "dump": "vidage",
                "station": "station", "pass": "passage", "doc": "document", "phase": "phase",
                "anomaly": "anomalie", "command": "commande", "gonogo": "GO/NO-GO",
                "gate": "jalon", "proposal": "proposition",
                "study_name": "étude", "tab": "onglet", "level": "niveau",
                "element": "élément", "decision": "sur"},
        "done": "fait", "not_done": "non fait",
    },
}

TOOL_ORDER = ("portal", "docs", "instructor", "mcs", "delayed_tm", "orbit", "radio", "design")

#: (worksheet id, question id, lang) -> (worksheet title, question text) | None
QuestionLookup = Callable[[str, str, str], "tuple[str, str] | None"]


def export_filename(fmt: str, now: datetime | None = None) -> str:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    ext = {"md": "md", "html": "html", "json": "json"}[fmt]
    return f"c2o-logbook-{now:%Y%m%d-%H%M}.{ext}"


def _hm(ts: str | None) -> str:
    d = parse_ts(ts)
    return d.strftime("%H:%M") if d else ""


def _when(ts: str | None) -> str:
    d = parse_ts(ts)
    return d.strftime("%Y-%m-%d %H:%M UTC") if d else ""


def _grouped(entries: list[dict]):
    """day -> tool -> (free entries oldest first, {ws id: [answers]})."""
    days: "OrderedDict[str, OrderedDict[str, tuple[list, OrderedDict]]]" = OrderedDict()
    for e in sorted(entries, key=lambda e: e.get("ts") or ""):
        d = parse_ts(e.get("ts"))
        day = d.strftime("%Y-%m-%d") if d else "—"
        tools = days.setdefault(day, OrderedDict())
        free, sheets = tools.setdefault(e.get("tool") or "?", ([], OrderedDict()))
        ws = e.get("worksheet") if e.get("kind") == "worksheet" else None
        if ws and ws.get("id"):
            sheets.setdefault(ws["id"], []).append(e)
        else:
            free.append(e)
    for day in days:
        days[day] = OrderedDict(sorted(days[day].items(),
                                       key=lambda kv: TOOL_ORDER.index(kv[0]) if kv[0] in TOOL_ORDER else 99))
    return days


def _header(summary: dict, person_label: str, lang: str, now: datetime) -> dict:
    L = LABELS[lang]
    tools = []
    for e in summary["entries"]:
        if e.get("tool") not in tools:
            tools.append(e.get("tool"))
    tools.sort(key=lambda t: TOOL_ORDER.index(t) if t in TOOL_ORDER else 99)
    return {
        "person": L["this_browser"] if person_label == "this browser" else person_label,
        "exported": now.strftime("%Y-%m-%d %H:%M"),
        "tools": ", ".join(L["tool"].get(t, t) for t in tools) or "—",
        "count": len(summary["entries"]),
        "footer": (L["deleted"].format(when=_when(summary.get("expires_at")))
                   if summary.get("expires_at") else L["not_scheduled"]),
    }


def _ws_text(e: dict, lookup: QuestionLookup | None, lang: str) -> tuple[str, str]:
    ws = e.get("worksheet") or {}
    hit = lookup(ws.get("id", ""), ws.get("q", ""), lang) if lookup else None
    title = (hit[0] if hit and hit[0] else ws.get("title")) or ws.get("id", "")
    q = (hit[1] if hit and hit[1] else ws.get("q_text")) or ws.get("q", "")
    return title, q


def _ctx_line(e: dict, lang: str) -> str:
    L = LABELS[lang]["ctx"]
    ctx = e.get("context") or {}
    # SpaceCDF entries carry both study_id (a UUID) and study_name: show the name.
    hidden = {"study_id"} if ctx.get("study_name") else set()
    parts = [f"{L.get(k, k)} {v}" for k, v in ctx.items()
             if v not in (None, "") and k not in hidden]
    if e.get("sim_ts"):
        parts.append(f"{LABELS[lang]['sim']} {e['sim_ts']}")
    return " · ".join(parts)


def _check_mark(e: dict, lang: str) -> str:
    c = (e.get("worksheet") or {}).get("checked")
    if c is True:
        return "[x] "
    if c is False:
        return "[ ] "
    return ""


def to_markdown(summary: dict, person_label: str, *, lang: str = "en",
                lookup: QuestionLookup | None = None, now: datetime | None = None) -> str:
    lang = "fr" if lang == "fr" else "en"
    L = LABELS[lang]
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    h = _header(summary, person_label, lang, now)
    c = "\u00a0: " if lang == "fr" else ": "      # French typography: space before ':'
    out = [f"# {L['title']}", "",
           f"- {L['person']}{c}{h['person']}",
           f"- {L['exported']}{c}{h['exported']}",
           f"- {L['tools']}{c}{h['tools']}",
           f"- {L['entries']}{c}{h['count']}", "",
           f"_{L['private']}_", ""]
    if not summary["entries"]:
        out += [L["empty"], ""]
    for day, tools in _grouped(summary["entries"]).items():
        out += [f"## {day}", ""]
        for tool, (free, sheets) in tools.items():
            out += [f"### {L['tool'].get(tool, tool)}", ""]
            for e in free:
                head = f"**{_hm(e.get('ts'))} · {L['kind'].get(e.get('kind'), e.get('kind'))}**"
                ctx = _ctx_line(e, lang)
                out.append(head + (f" ({ctx})" if ctx else "")
                           + (f" _{L['edited']}_" if e.get("edited") else ""))
                out.append("")
                out += [ln for ln in (e.get("text") or "").splitlines()] + [""]
            for wid, answers in sheets.items():
                title = _ws_text(answers[0], lookup, lang)[0]
                out += [f"#### {wid} — {title}", ""]
                for e in answers:
                    q = _ws_text(e, lookup, lang)[1]
                    out.append(f"- **{q}** ({_hm(e.get('ts'))})  ")
                    body = (e.get("text") or "").splitlines() or [""]
                    out.append("  " + _check_mark(e, lang) + body[0] + ("  " if len(body) > 1 else ""))
                    out += ["  " + ln + "  " for ln in body[1:]]
                out.append("")
    out += ["---", "", f"_{h['footer']}_", ""]
    return "\n".join(out)


_PRINT_CSS = """
@page{size:auto;margin:16mm 14mm}
*{box-sizing:border-box}
html{color:#141619;background:#fff}
body{font:10.5pt/1.45 'IBM Plex Sans',system-ui,-apple-system,'Segoe UI',sans-serif;margin:0 auto;
  max-width:182mm;padding:12mm 0}
header{border-bottom:1px solid #383C42;padding-bottom:3mm;margin-bottom:5mm}
h1{font-size:16pt;font-weight:600;margin:0 0 2mm;letter-spacing:-.01em}
dl{display:grid;grid-template-columns:max-content 1fr;gap:1mm 5mm;margin:0;font-size:9.5pt}
dt{color:#4A4F56}dd{margin:0}
.priv{font-size:9pt;color:#4A4F56;margin:2mm 0 0}
h2{font-size:12.5pt;font-weight:600;margin:7mm 0 2mm;padding-bottom:1mm;border-bottom:1px solid #B8BEC6;
  break-after:avoid}
h3{font-size:11pt;font-weight:600;margin:4mm 0 1.5mm;color:#383C42;break-after:avoid}
h4{font-size:10pt;font-weight:600;margin:3mm 0 1mm;break-after:avoid}
.e{display:grid;grid-template-columns:13mm 1fr;gap:0 3mm;padding:1.6mm 0;border-top:1px solid #E3E6EA;
  break-inside:avoid}
.t{font-family:'IBM Plex Mono',ui-monospace,Menlo,Consolas,monospace;font-size:9pt;color:#4A4F56}
.k{font-weight:600}.c{color:#4A4F56;font-size:9pt}
.x{white-space:pre-wrap;overflow-wrap:anywhere;margin-top:.5mm}
.q{font-weight:500}
.ed{font-style:italic;color:#4A4F56;font-size:9pt}
code,.id{font-family:'IBM Plex Mono',ui-monospace,Menlo,Consolas,monospace;font-size:9pt}
footer{margin-top:8mm;padding-top:2mm;border-top:1px solid #383C42;font-size:9pt;color:#383C42}
@media screen{body{padding:12mm 16px}}
"""


def to_html(summary: dict, person_label: str, *, lang: str = "en",
            lookup: QuestionLookup | None = None, now: datetime | None = None) -> str:
    lang = "fr" if lang == "fr" else "en"
    L = LABELS[lang]
    esc = html.escape
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    h = _header(summary, person_label, lang, now)
    body = [f"<header><h1>{esc(L['title'])}</h1><dl>",
            f"<dt>{esc(L['person'])}</dt><dd>{esc(h['person'])}</dd>",
            f"<dt>{esc(L['exported'])}</dt><dd class='id'>{esc(h['exported'])}</dd>",
            f"<dt>{esc(L['tools'])}</dt><dd>{esc(h['tools'])}</dd>",
            f"<dt>{esc(L['entries'])}</dt><dd class='id'>{h['count']}</dd></dl>",
            f"<p class='priv'>{esc(L['private'])}</p></header><main>"]
    if not summary["entries"]:
        body.append(f"<p>{esc(L['empty'])}</p>")
    for day, tools in _grouped(summary["entries"]).items():
        body.append(f"<section><h2 class='id'>{esc(day)}</h2>")
        for tool, (free, sheets) in tools.items():
            body.append(f"<h3>{esc(L['tool'].get(tool, tool))}</h3>")
            for e in free:
                ctx = _ctx_line(e, lang)
                body.append(
                    f"<div class='e'><span class='t'>{esc(_hm(e.get('ts')))}</span><div>"
                    f"<span class='k'>{esc(L['kind'].get(e.get('kind'), e.get('kind') or ''))}</span>"
                    + (f" <span class='c'>· {esc(ctx)}</span>" if ctx else "")
                    + (f" <span class='ed'>{esc(L['edited'])}</span>" if e.get("edited") else "")
                    + f"<div class='x'>{esc(e.get('text') or '')}</div></div></div>")
            for wid, answers in sheets.items():
                title = _ws_text(answers[0], lookup, lang)[0]
                body.append(f"<h4><span class='id'>{esc(wid)}</span> — {esc(title)}</h4>")
                for e in answers:
                    q = _ws_text(e, lookup, lang)[1]
                    c = (e.get("worksheet") or {}).get("checked")
                    mark = ("☑ " if c is True else "☐ " if c is False else "")
                    body.append(
                        f"<div class='e'><span class='t'>{esc(_hm(e.get('ts')))}</span><div>"
                        f"<div class='q'>{esc(q)}</div>"
                        f"<div class='x'>{esc(mark)}{esc(e.get('text') or '')}</div></div></div>")
        body.append("</section>")
    body.append(f"</main><footer>{esc(h['footer'])}</footer>")
    return ("<!DOCTYPE html>\n"
            f"<html lang='{lang}'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{esc(L['title'])} {esc(h['exported'])}</title>"
            f"<style>{_PRINT_CSS}</style></head><body>" + "".join(body) + "</body></html>\n")


def to_json(summary: dict, person_label: str, *, lang: str = "en",
            lookup: QuestionLookup | None = None, now: datetime | None = None) -> str:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    entries = []
    for e in sorted(summary["entries"], key=lambda e: e.get("ts") or ""):
        e = dict(e)
        if e.get("worksheet") and lookup:
            title, q = _ws_text(e, lookup, lang)
            e["worksheet"] = {**e["worksheet"], "title": title, "q_text": q}
        entries.append(e)
    doc = {"v": 1, "person": person_label, "exported_at": iso(now),
           "expires_at": summary.get("expires_at"), "retention_h": summary.get("retention_h"),
           "count": len(entries), "entries": entries}
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
