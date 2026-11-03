"""Post-session export: the edit timeline per person × seat (CSV and Markdown).

Teachers mostly use dashboards after class (LMU study, roles_and_consoles.md §5), so the
export lists every seat event — claims, edits, proposals, reviews, gate actions,
interventions — grouped by person and seat, with counts first.
"""
from __future__ import annotations

import csv
import io
import json
from collections import Counter, defaultdict
from typing import Any

from . import config as cfg

_LABELS = {
    "en": {"title": "SpaceCDF session timeline", "study": "Study", "person": "Person", "seat": "Seat",
           "events": "Events", "edits": "Edits", "proposals": "Proposals", "reviews": "Reviews",
           "first": "First", "last": "Last", "time": "Time (UTC)", "action": "Action", "target": "Target",
           "detail": "Detail", "summary": "Summary per person × seat", "unverified": "unverified name",
           "no_seat": "(no seat)", "generated": "Generated"},
    "fr": {"title": "Chronologie de la séance SpaceCDF", "study": "Étude", "person": "Personne", "seat": "Poste",
           "events": "Événements", "edits": "Modifications", "proposals": "Propositions", "reviews": "Revues",
           "first": "Premier", "last": "Dernier", "time": "Heure (UTC)", "action": "Action", "target": "Objet",
           "detail": "Détail", "summary": "Synthèse par personne × poste", "unverified": "nom non vérifié",
           "no_seat": "(sans poste)", "generated": "Généré le"},
}

EDIT_ACTIONS = {"edit", "write", "delete_element"}
REVIEW_ACTIONS = {"accept", "reject"}


def _seat_name(seat_id: str, lang: str) -> str:
    if not seat_id:
        return _LABELS[lang]["no_seat"]
    return cfg.label(seat_id).get(lang) or seat_id


def _detail(ev: dict[str, Any]) -> str:
    d = dict(ev.get("detail") or {})
    keep = {k: d[k] for k in ("param_keys", "new", "old", "owner_seat", "by_name", "by_seat", "comment", "note",
                              "to_name", "from_names", "text", "status") if d.get(k) not in (None, "", [], {})}
    return json.dumps(keep, ensure_ascii=False, sort_keys=True) if keep else ""


def to_csv(events: list[dict[str, Any]], study_names: dict[str, str], lang: str = "en") -> str:
    L = _LABELS["fr" if lang == "fr" else "en"]
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow([L["time"], L["study"], "study_id", L["person"], "person_id", "verified", L["seat"], "seat_id",
                L["action"], L["target"], L["detail"]])
    for ev in events:
        w.writerow([ev["ts"], study_names.get(ev["study_id"], ev["study_id"]), ev["study_id"],
                    ev["person_name"], ev["person_id"], "yes" if ev.get("verified") else "no",
                    _seat_name(ev["seat_id"], "fr" if lang == "fr" else "en"), ev["seat_id"],
                    ev["action"], ev["target"], _detail(ev)])
    return buf.getvalue()


def to_markdown(events: list[dict[str, Any]], study_names: dict[str, str], lang: str = "en",
                generated: str = "") -> str:
    lang = "fr" if lang == "fr" else "en"
    L = _LABELS[lang]
    out = [f"# {L['title']}", ""]
    if generated:
        out += [f"{L['generated']} {generated}", ""]
    by_study: dict[str, list[dict]] = defaultdict(list)
    for ev in events:
        by_study[ev["study_id"]].append(ev)
    for sid, evs in by_study.items():
        out += [f"## {L['study']}: {study_names.get(sid, sid)} (`{sid}`)", "", f"### {L['summary']}", ""]
        out += [f"| {L['person']} | {L['seat']} | {L['events']} | {L['edits']} | {L['proposals']} | "
                f"{L['reviews']} | {L['first']} | {L['last']} |",
                "|---|---|---:|---:|---:|---:|---|---|"]
        groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
        names: dict[str, tuple[str, bool]] = {}
        for ev in evs:
            groups[(ev["person_id"], ev["seat_id"])].append(ev)
            names[ev["person_id"]] = (ev["person_name"], bool(ev.get("verified")))
        for (pid, seat), g in sorted(groups.items(), key=lambda kv: (names[kv[0][0]][0].lower(), kv[0][1])):
            c = Counter(e["action"] for e in g)
            nm, ver = names[pid]
            who = nm or pid
            if not ver and pid:
                who += f" ({L['unverified']})"
            out.append(f"| {who} | {_seat_name(seat, lang)} | {len(g)} | {sum(c[a] for a in EDIT_ACTIONS)} | "
                       f"{c['propose']} | {sum(c[a] for a in REVIEW_ACTIONS)} | {g[0]['ts'][:19]} | {g[-1]['ts'][:19]} |")
        out.append("")
        for (pid, seat), g in sorted(groups.items(), key=lambda kv: (names[kv[0][0]][0].lower(), kv[0][1])):
            nm, _ = names[pid]
            out += [f"### {nm or pid} — {_seat_name(seat, lang)}", ""]
            for e in g:
                det = _detail(e)
                line = f"- `{e['ts'][11:19]}` **{e['action']}** {e['target']}".rstrip()
                if det:
                    line += f" — {det}"
                out.append(line)
            out.append("")
    if not by_study:
        out.append("—")
    return "\n".join(out) + "\n"
