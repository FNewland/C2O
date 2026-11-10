"""SpaceCDF Word document family: trade-off report (W6.03, Nov 2026; gate product ``trade_reports``).

``generate_trades_docx(sx, lang)`` — every trade of the study (``export_context`` section
``trades``): a summary table, then per trade the criteria with their weights (from pairwise
comparison or typed), the option scores against the datum with the weighted totals, the
thresholds, the weight sensitivity, the decision with its rationale and decision record, and the
requirements, risks and elements the trade affects. EN or FR headings; identifiers stay as entered.
Owner: agent D (W0_SEAMS.md).
"""
from __future__ import annotations

import io
from typing import Any

from docx import Document

from ._common import _add_cover_page, _add_footer, _add_section, _add_table, _add_toc_placeholder, _setup_margins, _setup_styles

_T = {
    "en": {
        "title": "Trade-off Reports", "std": "ECSS-E-ST-10C (trade-off reports)",
        "s1": "Summary", "intro": "Each trade compares its options against a datum (the reference option) with a "
        "weighted Pugh matrix: scores from -2 (much worse) to +2 (much better), weights from pairwise comparison of "
        "the criteria. The datum scores 0. An option below a criterion's threshold is not acceptable.",
        "id": "Trade", "trade": "Title", "seat": "Owner seat", "winner": "Highest score", "decision": "Decision",
        "status": "Status", "criteria": "Criteria and weights", "criterion": "Criterion", "weight": "Weight",
        "threshold": "Threshold", "scores": "Scores against the datum", "option": "Option", "total": "Weighted total",
        "unweighted": "Unweighted", "datum": "datum", "sens": "Weight sensitivity", "change": "Weight change that "
        "changes the leader", "new": "New leader", "robust": "Robust (no change within ±10 points)",
        "not_robust": "Sensitive: a change of 10 points or less in one weight changes the leader",
        "dec": "Decision", "selected": "Selected", "rationale": "Rationale", "record": "Decision record",
        "links": "Affected items", "reqs": "Requirements", "risks": "Risks", "elements": "Elements",
        "evidence": "Evidence", "note": "Note", "none": "None", "open": "open", "decided": "decided",
        "pairwise": "pairwise comparison", "direct": "typed weights", "method": "Weights from",
        "below": "below threshold", "no_trades": "The study has no trade studies yet.",
        "level": "Level", "differs": "The decision differs from the highest score; the rationale explains why.",
    },
    "fr": {
        "title": "Rapports de compromis", "std": "ECSS-E-ST-10C (rapports de compromis)",
        "s1": "Synthèse", "intro": "Chaque compromis compare ses options à une référence (l’option de base) avec une "
        "matrice de Pugh pondérée : notes de -2 (bien moins bon) à +2 (bien meilleur), poids obtenus par comparaison "
        "deux à deux des critères. La référence vaut 0. Une option sous le seuil d’un critère n’est pas acceptable.",
        "id": "Compromis", "trade": "Titre", "seat": "Poste responsable", "winner": "Meilleure note",
        "decision": "Décision", "status": "État", "criteria": "Critères et poids", "criterion": "Critère",
        "weight": "Poids", "threshold": "Seuil", "scores": "Notes par rapport à la référence", "option": "Option",
        "total": "Total pondéré", "unweighted": "Non pondéré", "datum": "référence", "sens": "Sensibilité aux poids",
        "change": "Variation de poids qui change l’option en tête", "new": "Nouvelle option en tête",
        "robust": "Robuste (aucun changement à ±10 points)",
        "not_robust": "Sensible : une variation de 10 points ou moins d’un poids change l’option en tête",
        "dec": "Décision", "selected": "Option retenue", "rationale": "Justification", "record": "Fiche de décision",
        "links": "Éléments concernés", "reqs": "Exigences", "risks": "Risques", "elements": "Éléments",
        "evidence": "Éléments probants", "note": "Remarque", "none": "Aucun", "open": "ouvert", "decided": "décidé",
        "pairwise": "comparaison deux à deux", "direct": "poids saisis", "method": "Poids obtenus par",
        "below": "sous le seuil", "no_trades": "L’étude ne contient encore aucun compromis.",
        "level": "Niveau", "differs": "La décision diffère de la meilleure note ; la justification explique pourquoi.",
    },
}


def _pts(x: float) -> str:
    return f"{x * 100:+.0f}"


def generate_trades_docx(sx: Any, lang: str = "en") -> bytes:
    t = _T.get(lang, _T["en"])
    doc = Document()
    _setup_styles(doc)
    _setup_margins(doc)
    name = getattr(sx, "study_name", "") or ""
    _add_cover_page(doc, t["title"], t["std"], name)
    _add_toc_placeholder(doc)
    _add_footer(doc, name)
    items = (getattr(sx, "trades", None) or {}).get("items") or []
    reqs = {str(r.get("code")): r for r in (getattr(sx, "requirements", None) or {}).get("items") or [] if r.get("code")}
    risks = {str(r.get("id")): r for r in (getattr(sx, "risks", None) or {}).get("items") or []}

    _add_section(doc, "1", t["s1"], t["intro"])
    if not items:
        doc.add_paragraph(t["no_trades"])
    else:
        _add_table(doc, [t["id"], t["trade"], t["seat"], t["winner"], t["decision"], t["status"]],
                   [[it["id"], (it.get("state") or {}).get("title", ""), (it.get("state") or {}).get("seat", ""),
                     (it.get("evaluation") or {}).get("winner") or "",
                     ((it.get("state") or {}).get("decision") or {}).get("selected") or "",
                     t.get((it.get("state") or {}).get("status", "open"), "")] for it in items])

    for n, it in enumerate(items, 2):
        st, ev = it.get("state") or {}, it.get("evaluation") or {}
        _add_section(doc, str(n), f"{it['id']} {st.get('title', '')}".strip())
        meta = [[t["seat"], st.get("seat") or "—"], [t["level"], st.get("level") or "—"],
                [t["method"], t["pairwise"] if ev.get("weights_source") == "pairwise" else t["direct"]]]
        _add_table(doc, ["", ""], meta)

        _add_section(doc, f"{n}.1", t["criteria"])
        w = ev.get("weights") or {}
        thr = st.get("thresholds") or {}
        _add_table(doc, [t["criterion"], t["weight"], t["threshold"]],
                   [[c, f"{100 * w.get(c, 0):.0f} %", f"{thr[c]:+g}" if c in thr else "—"] for c in st.get("criteria") or []])

        _add_section(doc, f"{n}.2", t["scores"])
        crit = st.get("criteria") or []
        totals = {x["option"]: x for x in ev.get("totals") or []}
        rows = []
        for o in st.get("options") or []:
            tot = totals.get(o) or {}
            sc = (st.get("scores") or {}).get(o) or {}
            label = f"{o} ({t['datum']})" if tot.get("datum") else o
            if tot.get("below_threshold"):
                label += f" [{t['below']}: {', '.join(tot['below_threshold'])}]"
            rows.append([label, *[("0" if tot.get("datum") else f"{sc.get(c, 0):+g}") for c in crit],
                         f"{tot.get('weighted', 0):+.2f}", f"{tot.get('unweighted', 0):+g}"])
        _add_table(doc, [t["option"], *crit, t["total"], t["unweighted"]], rows)

        _add_section(doc, f"{n}.3", t["sens"], t["robust"] if ev.get("robust") else t["not_robust"])
        srows = []
        for s in ev.get("sensitivity") or []:
            f = s.get("flip")
            srows.append([s["criterion"], f"{100 * s['weight']:.0f} %",
                          (_pts(f["delta"]) + " pts") if f else "—", (f or {}).get("new_winner") or "—"])
        if srows:
            _add_table(doc, [t["criterion"], t["weight"], t["change"], t["new"]], srows)

        _add_section(doc, f"{n}.4", t["dec"])
        dec = st.get("decision") or {}
        drows = [[t["selected"], dec.get("selected") or "—"], [t["rationale"], dec.get("rationale") or "—"],
                 [t["record"], dec.get("record_id") or (st.get("links") or {}).get("decision_record") or "—"]]
        _add_table(doc, ["", ""], drows)
        if ev.get("decision_differs_from_winner"):
            doc.add_paragraph(t["differs"])
        for key in ("evidence", "note"):
            if st.get(key):
                doc.add_paragraph(f"{t[key]}: {st[key]}")

        _add_section(doc, f"{n}.5", t["links"])
        links = st.get("links") or {}
        lrows = [[c, (reqs.get(c) or {}).get("text", "")] for c in links.get("requirements") or []]
        if lrows:
            _add_table(doc, [t["reqs"], ""], lrows)
        krows = [[r, (risks.get(r) or {}).get("description", "")] for r in links.get("risks") or []]
        if krows:
            _add_table(doc, [t["risks"], ""], krows)
        if links.get("elements"):
            names = it.get("element_names") or {}
            doc.add_paragraph(f"{t['elements']}: {', '.join(names.get(e, e) for e in links['elements'])}")
        if not (lrows or krows or links.get("elements")):
            doc.add_paragraph(t["none"])

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
