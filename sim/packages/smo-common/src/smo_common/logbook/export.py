"""Logbook exports: Markdown, print-ready HTML and JSON (LOGBOOK_SPEC §3).

The document reads like a completed course workbook (ops workbook, Franz
2026-11-02: "I want the teams to really use them as work books"):

1. a header: person, team, position, scenario, session, export time (UTC),
   tools used, entry count;
2. **Workbook** — the worksheets, in the printed workbook's order
   (``order``: the worksheet catalogue's file order, which follows the
   workbook numbering). A procedure checklist is a table per run (step,
   check, observed value, time UTC · sim, by, result, note); a form
   (anomaly ticket, handover, scorecard, briefing, debrief) is a
   field/entry table per filled copy; plain answers are listed under
   their question;
3. **Log** — every other entry, chronologically, by session day (UTC).

A footer gives the server deletion time. The HTML is self-contained (no
script, no external asset) and prints cleanly to A4 or Letter, so the
browser's "Save as PDF" makes the PDF. ``sheet=`` limits a document to one
worksheet ("Download this sheet").

Records written before the workbook (no ``check`` / ``form``) export as
before: a worksheet answer under its question.
"""
from __future__ import annotations

import html
import json
import re
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Callable

from .store import iso, parse_ts

__all__ = ["export_filename", "to_html", "to_json", "to_markdown", "LABELS", "build_document"]

#: Every label an export prints, EN and FR.
LABELS = {
    "en": {
        "title": "C2O logbook", "person": "Person", "exported": "Exported (UTC)",
        "tools": "Tools", "entries": "Entries", "deleted": "Deleted from the C2O server on {when}",
        "not_scheduled": "Nothing is stored on the C2O server for this logbook.",
        "private": "Private to you. Hand this file in if it is to be graded.",
        "sim": "sim time", "edited": "edited", "worksheets": "Worksheets",
        "this_browser": "this browser", "empty": "No entries.", "context": "Context",
        "team": "Team", "position": "Position", "scenario": "Scenario", "session": "Session",
        "workbook": "Workbook", "log": "Log", "sheet_only": "Worksheet {id} only",
        "run": "Run {run}", "started": "started", "by_runner": "runner", "by_operator": "operator",
        "col": {"n": "#", "step": "Step", "check": "Check (expected)", "value": "Observed",
                "time": "Time (UTC · sim)", "by": "By", "result": "Result", "note": "Note"},
        "field": "Field", "entry": "Entry", "printed_ref": "Printed sheet",
        "from_console": "prefilled from the console",
        "deviations": "Deviations", "not_reached": "not reached",
        "decisions": "Decisions recorded on this card",
        "result": {"pass": "PASS", "fail": "FAIL", "skip": "SKIPPED", "go": "GO",
                   "nogo": "NO-GO", "done": "done", "open": "open"},
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
                "element": "element", "decision": "on", "run": "run"},
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
        "team": "Équipe", "position": "Poste", "scenario": "Scénario", "session": "Séance",
        "workbook": "Cahier d’exercices", "log": "Journal", "sheet_only": "Fiche {id} seulement",
        "run": "Exécution {run}", "started": "commencée", "by_runner": "automate",
        "by_operator": "opérateur",
        "col": {"n": "nº", "step": "Étape", "check": "Vérification (attendu)", "value": "Observé",
                "time": "Heure (UTC · sim)", "by": "Par", "result": "Résultat", "note": "Note"},
        "field": "Champ", "entry": "Inscription", "printed_ref": "Fiche imprimée",
        "from_console": "prérempli depuis la console",
        "deviations": "Écarts", "not_reached": "non atteinte",
        "decisions": "Décisions consignées sur cette carte",
        "result": {"pass": "CONFORME", "fail": "NON CONFORME", "skip": "SAUTÉE", "go": "GO",
                   "nogo": "NO-GO", "done": "faite", "open": "ouverte"},
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
                "element": "élément", "decision": "sur", "run": "exécution"},
        "done": "fait", "not_done": "non fait",
    },
}

TOOL_ORDER = ("portal", "docs", "instructor", "mcs", "delayed_tm", "orbit", "radio", "design")
DEVIATIONS = ("fail", "skip", "nogo")

#: (worksheet id, question id, lang) -> (worksheet title, question text) | None
QuestionLookup = Callable[[str, str, str], "tuple[str, str] | None"]
#: worksheet id -> sort key (the printed workbook's order)
SheetOrder = Callable[[str], int]


def export_filename(fmt: str, now: datetime | None = None, sheet: str | None = None) -> str:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    ext = {"md": "md", "html": "html", "json": "json"}[fmt]
    tag = "-" + re.sub(r"[^A-Za-z0-9.-]", "_", sheet)[:40] if sheet else ""
    return f"c2o-logbook{tag}-{now:%Y%m%d-%H%M}.{ext}"


def _hm(ts: str | None) -> str:
    d = parse_ts(ts)
    return d.strftime("%H:%M") if d else ""


def _hms(ts: str | None) -> str:
    d = parse_ts(ts)
    return d.strftime("%H:%M:%S") if d else ""


def _when(ts: str | None) -> str:
    d = parse_ts(ts)
    return d.strftime("%Y-%m-%d %H:%M UTC") if d else ""


def _natkey(s) -> list:
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", str(s or ""))]


def _sim_hms(s: str | None) -> str:
    """``2026-03-10T04:18:22Z`` -> ``04:18:22`` (sim time, as on the console)."""
    m = re.search(r"T(\d\d:\d\d:\d\d)", s or "")
    return m.group(1) if m else (s or "")


# ── document model (one model, three renderers) ────────────────────────

def _ws_text(e: dict, lookup: QuestionLookup | None, lang: str) -> tuple[str, str]:
    ws = e.get("worksheet") or {}
    hit = lookup(ws.get("id", ""), ws.get("q", ""), lang) if lookup else None
    title = (hit[0] if hit and hit[0] else ws.get("title")) or ws.get("id", "")
    q = (hit[1] if hit and hit[1] else ws.get("q_text")) or ws.get("q", "")
    return title, q


def _header(summary: dict, person_label: str, lang: str, now: datetime,
            extra: dict | None) -> dict:
    L = LABELS[lang]
    entries = summary["entries"]
    tools = []
    for e in entries:
        if e.get("tool") not in tools:
            tools.append(e.get("tool"))
    tools.sort(key=lambda t: TOOL_ORDER.index(t) if t in TOOL_ORDER else 99)
    extra = {k: str(v).strip()[:120] for k, v in (extra or {}).items() if v and str(v).strip()}

    def latest(key):
        for e in sorted(entries, key=lambda e: e.get("ts") or "", reverse=True):
            v = (e.get("context") or {}).get(key) or (e.get("check") or {}).get(key)
            if v:
                return str(v)
        return ""
    ts = sorted(e.get("ts") or "" for e in entries if e.get("ts"))
    session = extra.get("session") or (
        f"{_when(ts[0])[:16]} – {_hm(ts[-1])} UTC" if ts else "")
    return {
        "person": L["this_browser"] if person_label == "this browser" else person_label,
        "team": extra.get("team", ""),
        "position": extra.get("position") or latest("position"),
        "scenario": extra.get("scenario") or latest("scenario"),
        "session": session,
        "exported": now.strftime("%Y-%m-%d %H:%M"),
        "tools": ", ".join(L["tool"].get(t, t) for t in tools) or "—",
        "count": len(entries),
        "footer": (L["deleted"].format(when=_when(summary.get("expires_at")))
                   if summary.get("expires_at") else L["not_scheduled"]),
    }


def build_document(summary: dict, person_label: str, *, lang: str = "en",
                   lookup: QuestionLookup | None = None, order: SheetOrder | None = None,
                   header: dict | None = None, sheet: str | None = None,
                   now: datetime | None = None) -> dict:
    """The export as data: ``{header, sheets: [...], log: [(day, [entries])]}``.

    Each sheet: ``{id, title, runs: [{run, started, rows}], forms: [...],
    answers: [(question, [entries])]}``.
    """
    lang = "fr" if lang == "fr" else "en"
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    entries = sorted(summary["entries"], key=lambda e: e.get("ts") or "")
    # Decisions recorded from a procedure card ("Record decision": context
    # procedure + run) belong to that run of the filled card, so they are
    # printed under its table instead of in the log.
    card_dec: dict[tuple[str, str], list] = {}
    for e in entries:
        ctx = e.get("context") or {}
        if e.get("kind") == "decision" and ctx.get("procedure") and ctx.get("run") not in (None, ""):
            card_dec.setdefault((str(ctx["procedure"]), str(ctx["run"])), []).append(e)
    if sheet:
        entries = [e for e in entries if (e.get("worksheet") or {}).get("id") == sheet]
    doc_summary = dict(summary, entries=entries)
    placed: set[str] = set()
    sheets: "OrderedDict[str, dict]" = OrderedDict()
    log: "OrderedDict[str, list]" = OrderedDict()
    for e in entries:
        ws = e.get("worksheet") if e.get("kind") == "worksheet" else None
        if not (ws and ws.get("id")):
            d = parse_ts(e.get("ts"))
            log.setdefault(d.strftime("%Y-%m-%d") if d else "—", []).append(e)
            continue
        wid = ws["id"]
        s = sheets.setdefault(wid, {"id": wid, "title": "", "runs": OrderedDict(),
                                    "forms": [], "answers": OrderedDict(), "first": e.get("ts")})
        title = _ws_text(e, lookup, lang)[0]
        if title and (not s["title"] or s["title"] == wid):
            s["title"] = title
        if isinstance(e.get("check"), dict):
            c = e["check"]
            run = ws.get("instance") or c.get("run") or "1"
            r = s["runs"].setdefault(run, {"run": run, "procedure": c.get("procedure", ""),
                                           "started": e.get("ts"), "rows": []})
            r["rows"].append(e)
        elif isinstance(e.get("form"), dict):
            s["forms"].append(e)
        else:
            s["answers"].setdefault(ws.get("q") or "", []).append(e)
    out_sheets = []
    for wid, s in sheets.items():
        for r in s["runs"].values():
            # prerequisites first, then the steps in card order
            r["rows"].sort(key=lambda e: (
                0 if e["check"].get("part") == "pre" else 1,
                e["check"]["order"] if isinstance(e["check"].get("order"), int) else 10 ** 6,
                _natkey(e["check"].get("step") or e["check"].get("key")), e.get("ts") or ""))
            r["decisions"] = card_dec.get((str(r["procedure"]), str(r["run"])), [])
            placed.update(e.get("id") for e in r["decisions"])
        s["runs"] = list(s["runs"].values())
        s["answers"] = [(_ws_text(v[0], lookup, lang)[1], v) for v in s["answers"].values()]
        out_sheets.append(s)
    def sheet_key(s):
        k = order(s["id"]) if order else None
        return (k if k is not None else 10 ** 6, _natkey(s["id"]), s["first"] or "")
    out_sheets.sort(key=sheet_key)
    if placed:
        log = OrderedDict((d, [e for e in es if e.get("id") not in placed]) for d, es in log.items())
        log = OrderedDict((d, es) for d, es in log.items() if es)
    return {"lang": lang, "header": _header(doc_summary, person_label, lang, now, header),
            "sheet": sheet, "sheets": out_sheets, "log": list(log.items()), "summary": doc_summary}


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


def _check_mark(e: dict) -> str:
    c = (e.get("worksheet") or {}).get("checked")
    if c is True:
        return "[x] "
    if c is False:
        return "[ ] "
    return ""


def _row_cells(e: dict, lang: str) -> dict:
    """One checklist row as plain strings (both renderers)."""
    L = LABELS[lang]
    c = e.get("check") or {}
    ws = e.get("worksheet") or {}
    vals = c.get("values") or []
    check = "; ".join(v.get("expect") or v.get("param") or "" for v in vals if v.get("expect") or v.get("param"))
    observed = "; ".join(
        (f"{v.get('param')} = " if v.get("param") and len(vals) > 1 else "")
        + f"{v.get('value', '')}{(' ' + v['units']) if v.get('units') else ''}"
        + (" ✗" if v.get("ok") is False else "") + (" (stale)" if v.get("stale") else "")
        for v in vals if v.get("value") not in (None, ""))
    sim = _sim_hms(c.get("sim_ts") or e.get("sim_ts"))
    by = ", ".join(x for x in (c.get("position"),
                               L["by_runner"] if c.get("source") == "runner" else
                               L["by_operator"] if c.get("source") == "operator" else "") if x)
    res = c.get("result") or ("done" if ws.get("checked") else "open")
    step_label = c.get("step") or ""
    title = c.get("title") or re.sub(r"^\S+\s+—\s+", "", ws.get("q_text") or "")
    note = c.get("note") or ""
    return {"n": step_label, "step": title, "check": check, "value": observed,
            "time": _hms(e.get("updated_ts") or e.get("ts")) + (f" · {sim}" if sim else ""),
            "by": by, "result": L["result"].get(res, res), "deviation": res in DEVIATIONS,
            "note": note}


def _form_rows(e: dict, lookup: QuestionLookup | None, lang: str) -> list[tuple[str, str, bool]]:
    L = LABELS[lang]
    wid = (e.get("worksheet") or {}).get("id", "")
    rows = []
    for f in (e.get("form") or {}).get("fields") or []:
        hit = lookup(wid, f.get("q", ""), lang) if lookup else None
        label = (hit[1] if hit and hit[1] else f.get("label")) or f.get("q", "")
        v = f.get("value") or ""
        if isinstance(f.get("checked"), bool):
            v = ("☑ " if f["checked"] else "☐ ") + v
        rows.append((label, v.strip(), bool(f.get("prefilled"))))
    return rows


def _md_cell(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", "<br>").strip()


def to_markdown(summary: dict, person_label: str, *, lang: str = "en",
                lookup: QuestionLookup | None = None, now: datetime | None = None,
                order: SheetOrder | None = None, header: dict | None = None,
                sheet: str | None = None) -> str:
    doc = build_document(summary, person_label, lang=lang, lookup=lookup, order=order,
                         header=header, sheet=sheet, now=now)
    lang = doc["lang"]
    L = LABELS[lang]
    h = doc["header"]
    c = "\u00a0: " if lang == "fr" else ": "      # French typography: space before ':'
    out = [f"# {L['title']}", ""]
    out.append(f"- {L['person']}{c}{h['person']}")
    for k in ("team", "position", "scenario", "session"):
        if h[k]:
            out.append(f"- {L[k]}{c}{h[k]}")
    out += [f"- {L['exported']}{c}{h['exported']}",
            f"- {L['tools']}{c}{h['tools']}",
            f"- {L['entries']}{c}{h['count']}", ""]
    if doc["sheet"]:
        out += [f"_{L['sheet_only'].format(id=doc['sheet'])}_", ""]
    out += [f"_{L['private']}_", ""]
    if not doc["summary"]["entries"]:
        out += [L["empty"], ""]
    if doc["sheets"]:
        out += [f"## {L['workbook']}", ""]
    for s in doc["sheets"]:
        out += [f"### {s['id']} — {s['title']}" if s["title"] and s["title"] != s["id"]
                else f"### {s['id']}", ""]
        for r in s["runs"]:
            first = r["rows"][0] if r["rows"] else {}
            ctx = first.get("check") or {}
            out += [f"**{L['run'].format(run=r['run'])}**"
                    + (f" · {r['procedure']}" if r["procedure"] else "")
                    + f" · {L['started']} {_when(r['started'])}"
                    + (f" · {ctx.get('position')}" if ctx.get("position") else ""), ""]
            C = L["col"]
            out.append(f"| {C['n']} | {C['step']} | {C['check']} | {C['value']} | {C['time']} "
                       f"| {C['by']} | {C['result']} | {C['note']} |")
            out.append("|---|---|---|---|---|---|---|---|")
            devs = []
            for e in r["rows"]:
                rc = _row_cells(e, lang)
                res = f"**{rc['result']}**" if rc["deviation"] else rc["result"]
                out.append("| " + " | ".join(_md_cell(x) for x in (
                    rc["n"], rc["step"], rc["check"], rc["value"], rc["time"], rc["by"], res,
                    rc["note"])) + " |")
                if rc["deviation"]:
                    devs.append(f"{rc['n']} {rc['result']}" + (f": {rc['note']}" if rc["note"] else ""))
            out.append("")
            if devs:
                out += [f"_{L['deviations']}{c}{'; '.join(devs)}_", ""]
            if r.get("decisions"):
                out += [f"**{L['decisions']}**", ""]
                for e in r["decisions"]:
                    step = (e.get("context") or {}).get("step")
                    body = (e.get("text") or "").splitlines() or [""]
                    out.append(f"- {_hm(e.get('ts'))}" + (f" · {L['ctx']['step']} {step}" if step else "")
                               + f" — {body[0]}" + ("  " if len(body) > 1 else ""))
                    out += ["  " + ln + "  " for ln in body[1:]]
                out.append("")
        for e in s["forms"]:
            inst = (e.get("form") or {}).get("instance") or (e.get("worksheet") or {}).get("instance")
            out += [f"**{inst}** · {_when(e.get('updated_ts') or e.get('ts'))}" if inst
                    else f"_{_when(e.get('updated_ts') or e.get('ts'))}_", ""]
            for i in (e.get("form") or {}).get("info") or []:
                out.append(f"- {i['label']}{c}{i['value']}")
            if (e.get("form") or {}).get("info"):
                out.append("")
            out += [f"| {L['field']} | {L['entry']} |", "|---|---|"]
            for label, v, pre in _form_rows(e, lookup, lang):
                out.append(f"| {_md_cell(label)} | {_md_cell(v)}{' ¹' if pre and v else ''} |")
            out.append("")
            if any(pre for _, v, pre in _form_rows(e, lookup, lang) if v):
                out += [f"¹ _{L['from_console']}_", ""]
        for q, answers in s["answers"]:
            for e in answers:
                out.append(f"- **{q}** ({_hm(e.get('ts'))})  ")
                body = (e.get("text") or "").splitlines() or [""]
                out.append("  " + _check_mark(e) + body[0] + ("  " if len(body) > 1 else ""))
                out += ["  " + ln + "  " for ln in body[1:]]
            out.append("")
    if doc["log"]:
        out += [f"## {L['log']}", ""]
    for day, es in doc["log"]:
        out += [f"### {day}", ""]
        for e in es:
            head = (f"**{_hm(e.get('ts'))} · {L['tool'].get(e.get('tool'), e.get('tool'))} · "
                    f"{L['kind'].get(e.get('kind'), e.get('kind'))}**")
            ctx = _ctx_line(e, lang)
            out.append(head + (f" ({ctx})" if ctx else "")
                       + (f" _{L['edited']}_" if e.get("edited") else ""))
            out.append("")
            out += [ln for ln in (e.get("text") or "").splitlines()] + [""]
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
h2{font-size:13pt;font-weight:600;margin:8mm 0 2mm;padding-bottom:1mm;border-bottom:1px solid #383C42;
  break-after:avoid}
h3{font-size:11pt;font-weight:600;margin:5mm 0 1.5mm;padding-bottom:.6mm;border-bottom:1px solid #B8BEC6;
  break-after:avoid}
h4{font-size:10pt;font-weight:600;margin:3mm 0 1mm;break-after:avoid}
.e{display:grid;grid-template-columns:13mm 1fr;gap:0 3mm;padding:1.6mm 0;border-top:1px solid #E3E6EA;
  break-inside:avoid}
.t{font-family:'IBM Plex Mono',ui-monospace,Menlo,Consolas,monospace;font-size:9pt;color:#4A4F56}
.k{font-weight:600}.c{color:#4A4F56;font-size:9pt}
.x{white-space:pre-wrap;overflow-wrap:anywhere;margin-top:.5mm}
.q{font-weight:500}
.ed{font-style:italic;color:#4A4F56;font-size:9pt}
code,.id{font-family:'IBM Plex Mono',ui-monospace,Menlo,Consolas,monospace;font-size:9pt}
table{width:100%;border-collapse:collapse;font-size:8.8pt;margin:1mm 0 2mm;break-inside:auto}
th,td{border:1px solid #B8BEC6;padding:1mm 1.4mm;text-align:left;vertical-align:top;overflow-wrap:break-word}
table.cl{table-layout:fixed}
table.cl td.v{font-family:'IBM Plex Mono',ui-monospace,Menlo,Consolas,monospace;font-size:8pt}
th{background:#EEF0F3;font-weight:600}
tr{break-inside:avoid}
td.n,td.tm{font-family:'IBM Plex Mono',ui-monospace,Menlo,Consolas,monospace;font-size:8pt}
td.dev{font-weight:700}
.run{font-size:9.5pt;margin:2mm 0 1mm}
.devs{font-size:9pt;margin:0 0 2mm}
.pre{color:#4A4F56;font-size:8pt}
ul.info{margin:1mm 0;padding-left:5mm;font-size:9pt}
footer{margin-top:8mm;padding-top:2mm;border-top:1px solid #383C42;font-size:9pt;color:#383C42}
@media screen{body{padding:12mm 16px}}
"""


def to_html(summary: dict, person_label: str, *, lang: str = "en",
            lookup: QuestionLookup | None = None, now: datetime | None = None,
            order: SheetOrder | None = None, header: dict | None = None,
            sheet: str | None = None) -> str:
    doc = build_document(summary, person_label, lang=lang, lookup=lookup, order=order,
                         header=header, sheet=sheet, now=now)
    lang = doc["lang"]
    L = LABELS[lang]
    esc = html.escape
    h = doc["header"]
    body = [f"<header><h1>{esc(L['title'])}</h1><dl>",
            f"<dt>{esc(L['person'])}</dt><dd>{esc(h['person'])}</dd>"]
    for k in ("team", "position", "scenario", "session"):
        if h[k]:
            body.append(f"<dt>{esc(L[k])}</dt><dd>{esc(h[k])}</dd>")
    body += [f"<dt>{esc(L['exported'])}</dt><dd class='id'>{esc(h['exported'])}</dd>",
             f"<dt>{esc(L['tools'])}</dt><dd>{esc(h['tools'])}</dd>",
             f"<dt>{esc(L['entries'])}</dt><dd class='id'>{h['count']}</dd></dl>"]
    if doc["sheet"]:
        body.append(f"<p class='priv'>{esc(L['sheet_only'].format(id=doc['sheet']))}</p>")
    body.append(f"<p class='priv'>{esc(L['private'])}</p></header><main>")
    if not doc["summary"]["entries"]:
        body.append(f"<p>{esc(L['empty'])}</p>")
    if doc["sheets"]:
        body.append(f"<h2>{esc(L['workbook'])}</h2>")
    for s in doc["sheets"]:
        body.append(f"<section><h3><span class='id'>{esc(s['id'])}</span>"
                    + (f" — {esc(s['title'])}" if s["title"] and s["title"] != s["id"] else "")
                    + "</h3>")
        for r in s["runs"]:
            first = (r["rows"][0].get("check") or {}) if r["rows"] else {}
            body.append(f"<p class='run'><b>{esc(L['run'].format(run=r['run']))}</b>"
                        + (f" · {esc(r['procedure'])}" if r["procedure"] else "")
                        + f" · {esc(L['started'])} {esc(_when(r['started']))}"
                        + (f" · {esc(first.get('position'))}" if first.get("position") else "")
                        + "</p>")
            C = L["col"]
            body.append("<table class='cl'><colgroup><col style='width:5%'><col style='width:15%'>"
                        "<col style='width:21%'><col style='width:19%'><col style='width:11%'>"
                        "<col style='width:10%'><col style='width:8%'><col></colgroup><thead><tr>" + "".join(
                f"<th>{esc(C[k])}</th>" for k in ("n", "step", "check", "value", "time", "by",
                                                   "result", "note")) + "</tr></thead><tbody>")
            devs = []
            for e in r["rows"]:
                rc = _row_cells(e, lang)
                br = lambda x: "<br>".join(esc(p) for p in x.split("; "))   # noqa: E731
                body.append(
                    f"<tr><td class='n'>{esc(rc['n'])}</td><td>{esc(rc['step'])}</td>"
                    f"<td>{br(rc['check'])}</td><td class='v'>{br(rc['value'])}</td>"
                    f"<td class='tm'>{esc(rc['time']).replace(' · ', '<br>')}</td>"
                    f"<td>{esc(rc['by']).replace(', ', '<br>')}</td>"
                    f"<td{' class=dev' if rc['deviation'] else ''}>{esc(rc['result'])}</td>"
                    f"<td>{esc(rc['note'])}</td></tr>")
                if rc["deviation"]:
                    devs.append(f"{rc['n']} {rc['result']}" + (f": {rc['note']}" if rc["note"] else ""))
            body.append("</tbody></table>")
            if devs:
                body.append(f"<p class='devs'><b>{esc(L['deviations'])}</b> — {esc('; '.join(devs))}</p>")
            if r.get("decisions"):
                body.append(f"<h4>{esc(L['decisions'])}</h4>")
                for e in r["decisions"]:
                    step = (e.get("context") or {}).get("step")
                    body.append(
                        f"<div class='e'><span class='t'>{esc(_hm(e.get('ts')))}</span><div>"
                        + (f"<span class='c'>{esc(L['ctx']['step'])} {esc(str(step))}</span>" if step else "")
                        + f"<div class='x'>{esc(e.get('text') or '')}</div></div></div>")
        for e in s["forms"]:
            inst = (e.get("form") or {}).get("instance") or (e.get("worksheet") or {}).get("instance")
            body.append(f"<h4>{esc(inst) + ' · ' if inst else ''}<span class='id'>"
                        f"{esc(_when(e.get('updated_ts') or e.get('ts')))}</span></h4>")
            info = (e.get("form") or {}).get("info") or []
            if info:
                body.append("<ul class='info'>" + "".join(
                    f"<li>{esc(i['label'])} : {esc(i['value'])}</li>" if lang == "fr" else
                    f"<li>{esc(i['label'])}: {esc(i['value'])}</li>" for i in info) + "</ul>")
            body.append(f"<table><thead><tr><th>{esc(L['field'])}</th><th>{esc(L['entry'])}</th>"
                        "</tr></thead><tbody>")
            for label, v, pre in _form_rows(e, lookup, lang):
                body.append(f"<tr><td>{esc(label)}</td><td><span class='x'>{esc(v)}</span>"
                            + (f" <span class='pre'>({esc(L['from_console'])})</span>" if pre and v else "")
                            + "</td></tr>")
            body.append("</tbody></table>")
        for q, answers in s["answers"]:
            for e in answers:
                c = (e.get("worksheet") or {}).get("checked")
                mark = ("☑ " if c is True else "☐ " if c is False else "")
                body.append(
                    f"<div class='e'><span class='t'>{esc(_hm(e.get('ts')))}</span><div>"
                    f"<div class='q'>{esc(q)}</div>"
                    f"<div class='x'>{esc(mark)}{esc(e.get('text') or '')}</div></div></div>")
        body.append("</section>")
    if doc["log"]:
        body.append(f"<h2>{esc(L['log'])}</h2>")
    for day, es in doc["log"]:
        body.append(f"<section><h3 class='id'>{esc(day)}</h3>")
        for e in es:
            ctx = _ctx_line(e, lang)
            body.append(
                f"<div class='e'><span class='t'>{esc(_hm(e.get('ts')))}</span><div>"
                f"<span class='k'>{esc(L['tool'].get(e.get('tool'), e.get('tool') or ''))} · "
                f"{esc(L['kind'].get(e.get('kind'), e.get('kind') or ''))}</span>"
                + (f" <span class='c'>· {esc(ctx)}</span>" if ctx else "")
                + (f" <span class='ed'>{esc(L['edited'])}</span>" if e.get("edited") else "")
                + f"<div class='x'>{esc(e.get('text') or '')}</div></div></div>")
        body.append("</section>")
    body.append(f"</main><footer>{esc(h['footer'])}</footer>")
    return ("<!DOCTYPE html>\n"
            f"<html lang='{lang}'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{esc(L['title'])} {esc(h['exported'])}</title>"
            f"<style>{_PRINT_CSS}</style></head><body>" + "".join(body) + "</body></html>\n")


def to_json(summary: dict, person_label: str, *, lang: str = "en",
            lookup: QuestionLookup | None = None, now: datetime | None = None,
            order: SheetOrder | None = None, header: dict | None = None,
            sheet: str | None = None) -> str:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    entries = []
    for e in sorted(summary["entries"], key=lambda e: e.get("ts") or ""):
        if sheet and (e.get("worksheet") or {}).get("id") != sheet:
            continue
        e = dict(e)
        if e.get("worksheet") and lookup:
            title, q = _ws_text(e, lookup, lang)
            e["worksheet"] = {**e["worksheet"], "title": title, "q_text": q}
        entries.append(e)
    hd = _header(dict(summary, entries=entries), person_label, lang if lang == "fr" else "en",
                 now, header)
    doc = {"v": 1, "person": person_label, "exported_at": iso(now),
           "expires_at": summary.get("expires_at"), "retention_h": summary.get("retention_h"),
           "count": len(entries), "entries": entries}
    for k in ("team", "position", "scenario", "session"):
        if hd.get(k):
            doc[k] = hd[k]
    if sheet:
        doc["sheet"] = sheet
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
