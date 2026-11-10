"""SpaceCDF Word document family: gate review report (W4.08, Nov 2026).

``generate_review_report_docx(data, lang)`` — ``data`` is ``routers.gates.review_report_data``:
the gate evaluation (criteria with results and evidence, rule checks), the review record (chair
note, go / no-go, board), the RIDs and actions raised at the gate and those still open from
earlier gates, the gate history and the baseline diff against the previous gate. EN or FR
headings; criterion questions and identifiers stay as stored. Owner: agent D (W0_SEAMS.md).
"""
from __future__ import annotations

import io
from typing import Any

from docx import Document

from ._common import _add_cover_page, _add_footer, _add_section, _add_table, _setup_margins, _setup_styles

_T = {
    "en": {
        "title": "Review Report", "std": "ECSS-M-ST-10C Rev.1 (project reviews)", "s1": "Review",
        "gate": "Gate", "profile": "Gate profile", "state": "State", "decision": "Decision", "chair": "Chair note",
        "board": "Review board", "decided": "Decided", "s2": "Exit criteria", "id": "Id", "question": "Question",
        "result": "Result", "evidence": "Evidence", "owner": "Owner seat", "s2b": "Rule checks", "s3": "Open items",
        "open_intro": "Criteria that did not pass (failed, manual or not evaluated).", "s4": "RIDs and actions",
        "s4b": "Carried from earlier reviews (still open)", "number": "Number", "kind": "Kind",
        "raised": "Raised by", "desc": "Description", "severity": "Severity", "due": "Due", "status": "Status",
        "closure": "Closure evidence", "s5": "Baseline changes since the previous gate", "s6": "History",
        "none": "None.", "no_diff": "No earlier baseline to compare with (the gate before it has not been passed, "
        "or this gate has no baseline yet).", "added": "added", "removed": "removed", "changed": "changed",
        "area": "Area", "action": "Action", "at": "At", "by": "By", "summary": "Summary",
        "must": "Must-pass criteria met", "ready": "Ready for the review", "yes": "yes", "no": "no",
        "go": "GO", "go_with_actions": "GO with actions", "no_go": "NO GO", "pending": "not recorded",
        "requirements": "Requirements", "elements": "Elements", "risks": "Risks", "mission_need": "Mission need",
        "criteria": "Criteria results",
    },
    "fr": {
        "title": "Rapport de revue", "std": "ECSS-M-ST-10C Rev.1 (revues de projet)", "s1": "Revue",
        "gate": "Jalon", "profile": "Profil de jalons", "state": "État", "decision": "Décision",
        "chair": "Note du président", "board": "Comité de revue", "decided": "Décidé le", "s2": "Critères de sortie",
        "id": "Id", "question": "Question", "result": "Résultat", "evidence": "Éléments probants",
        "owner": "Poste responsable", "s2b": "Vérifications des règles", "s3": "Points ouverts",
        "open_intro": "Critères non satisfaits (en échec, manuels ou non évalués).", "s4": "RID et actions",
        "s4b": "Reportés des revues précédentes (encore ouverts)", "number": "Numéro", "kind": "Nature",
        "raised": "Émis par", "desc": "Description", "severity": "Gravité", "due": "Échéance", "status": "État",
        "closure": "Preuve de clôture", "s5": "Changements de référence depuis le jalon précédent", "s6": "Historique",
        "none": "Aucun.", "no_diff": "Aucune référence antérieure à comparer (le jalon précédent n’est pas franchi, "
        "ou ce jalon n’a pas encore de référence).", "added": "ajoutés", "removed": "retirés", "changed": "modifiés",
        "area": "Domaine", "action": "Action", "at": "Date", "by": "Par", "summary": "Synthèse",
        "must": "Critères obligatoires satisfaits", "ready": "Prêt pour la revue", "yes": "oui", "no": "non",
        "go": "GO", "go_with_actions": "GO avec actions", "no_go": "NO GO", "pending": "non enregistrée",
        "requirements": "Exigences", "elements": "Éléments", "risks": "Risques", "mission_need": "Besoin de mission",
        "criteria": "Résultats des critères",
    },
}


def _rid_rows(items: list[dict[str, Any]]) -> list[list[str]]:
    return [[r.get("number") or "", r.get("kind") or "", r.get("raised_by_seat") or r.get("raised_by") or "",
             r.get("description") or "", r.get("severity") or "", r.get("owner_seat") or "", r.get("due_date") or "",
             r.get("status") or "", r.get("closure_evidence") or ""] for r in items]


def generate_review_report_docx(data: dict[str, Any], lang: str = "en") -> bytes:
    t = _T.get(lang, _T["en"])
    ev = data.get("evaluation") or {}
    gate = ev.get("gate") or {}
    gname = (gate.get("name") or {}).get(lang) or (gate.get("name") or {}).get("en") or ""
    doc = Document()
    _setup_styles(doc)
    _setup_margins(doc)
    name = data.get("study_name") or ""
    _add_cover_page(doc, f"{gate.get('short', '')} {t['title']}", t["std"], name)
    _add_footer(doc, name)

    rev = data.get("review") or {}
    summ = ev.get("summary") or {}
    _add_section(doc, "1", t["s1"])
    _add_table(doc, ["", ""], [
        [t["gate"], f"{gate.get('short', '')} — {gname}"],
        [t["profile"], ((ev.get("profile") or {}).get("label") or {}).get(lang) or (ev.get("profile") or {}).get("id", "")],
        [t["state"], ev.get("state") or ""],
        [t["must"], f"{summ.get('must_pass_met', 0)} / {summ.get('must_pass', 0)}"],
        [t["ready"], t["yes"] if ev.get("ready") else t["no"]],
        [t["decision"], t.get(rev.get("decision") or "", t["pending"])],
        [t["decided"], rev.get("decided_at") or "—"],
        [t["board"], rev.get("board") or "—"],
        [t["chair"], rev.get("chair_note") or "—"],
    ])

    crit = ev.get("criteria") or []
    _add_section(doc, "2", t["s2"])
    _add_table(doc, [t["id"], t["question"], t["result"], t["evidence"], t["owner"]],
               [[c.get("id", ""), c.get("question", ""), (c.get("verdict") or c.get("status") or "").upper(),
                 c.get("evidence_found") or "", c.get("owner_seat") or ""] for c in crit])
    checks = ev.get("checks") or []
    if checks:
        _add_section(doc, "2.1", t["s2b"])
        _add_table(doc, [t["id"], t["question"], t["result"]],
                   [[c.get("id", ""), ((c.get("label") or {}).get(lang) or (c.get("label") or {}).get("en", "")
                                       if isinstance(c.get("label"), dict) else str(c.get("label") or "")),
                     str(c.get("status", "")).upper()] for c in checks])

    _add_section(doc, "3", t["s3"], t["open_intro"])
    open_c = [c for c in crit if c.get("status") != "pass"]
    if open_c:
        _add_table(doc, [t["id"], t["question"], t["result"], t["owner"]],
                   [[c.get("id", ""), c.get("question", ""), (c.get("verdict") or c.get("status") or "").upper(),
                     c.get("owner_seat") or ""] for c in open_c])
    else:
        doc.add_paragraph(t["none"])

    heads = [t["number"], t["kind"], t["raised"], t["desc"], t["severity"], t["owner"], t["due"], t["status"], t["closure"]]
    _add_section(doc, "4", t["s4"])
    rids = data.get("rids") or []
    if rids:
        _add_table(doc, heads, _rid_rows(rids))
    else:
        doc.add_paragraph(t["none"])
    carried = data.get("carried") or []
    if carried:
        _add_section(doc, "4.1", t["s4b"])
        _add_table(doc, heads, _rid_rows(carried))

    _add_section(doc, "5", t["s5"])
    diff = data.get("diff")
    if not diff:
        doc.add_paragraph(t["no_diff"])
    else:
        ch = diff.get("changes") or {}
        rows = []
        for area in ("requirements", "elements", "risks"):
            d = ch.get(area) or {}
            for k in ("added", "removed", "changed"):
                if d.get(k):
                    rows.append([t[area], t[k], ", ".join(str(x) for x in d[k][:60]) + (" …" if len(d[k]) > 60 else "")])
        if ch.get("mission_need"):
            rows.append([t["mission_need"], t["changed"], ", ".join(ch["mission_need"])])
        if ch.get("criteria"):
            rows.append([t["criteria"], t["changed"], ", ".join(ch["criteria"])])
        if rows:
            _add_table(doc, [t["area"], "", ""], rows)
        else:
            doc.add_paragraph(t["none"])

    _add_section(doc, "6", t["s6"])
    hist = data.get("history") or []
    if hist:
        _add_table(doc, [t["action"], t["state"], t["at"], t["by"]],
                   [[h.get("action", ""), f"{h.get('from', '')} → {h.get('to', '')}", h.get("at", ""), h.get("by", "")]
                    for h in hist])
    else:
        doc.add_paragraph(t["none"])

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
