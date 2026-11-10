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
        "gate": "Review gate", "levels": {"mission": "mission", "system": "system", "architecture": "architecture",
                                         "subsystem": "subsystem", "equipment": "equipment"},
        "absolute": "absolute scale (1 to 5 per criterion)", "pugh": "weighted Pugh against the datum",
        "scoring": "Scoring", "source": "Source (MOE or requirement)", "scale": "Scale",
        "must": "Must-criteria (screening)", "screened": "screened out", "screened_h": "Options screened out",
        "reason": "Reason", "pm20": "Sensitivity to ±20 % on each weight", "factor": "Factor",
        "lead": "Lead over the next option", "robust20": "The winner is unchanged for every single weight ×0.8 and ×1.2.",
        "flips20": "The winner changes for: {flips}.", "breakeven": "Break-even: multiplier on one weight that lets "
        "the runner-up win", "multiplier": "Multiplier", "runner": "Runner-up", "margin": "Lead",
        "dissent": "Dissent", "conditions": "Acceptance conditions", "risks_sel": "Risks of the selected option",
        "recommendation": "Recommendation", "condition": "Condition", "due": "Due", "fallback": "Fallback",
        "posthoc": "The weights were changed after scoring.", "by_gate": "Trades by review gate",
        "question": "Decision to make",
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
        "gate": "Jalon de revue", "levels": {"mission": "mission", "system": "système", "architecture": "architecture",
                                            "subsystem": "sous-système", "equipment": "équipement"},
        "absolute": "échelle absolue (1 à 5 par critère)", "pugh": "Pugh pondéré par rapport à la référence",
        "scoring": "Notation", "source": "Source (MOE ou exigence)", "scale": "Échelle",
        "must": "Critères éliminatoires", "screened": "éliminée", "screened_h": "Options éliminées",
        "reason": "Motif", "pm20": "Sensibilité à ±20 % sur chaque poids", "factor": "Facteur",
        "lead": "Avance sur l’option suivante", "robust20": "L’option retenue ne change pour aucun poids ×0,8 ou ×1,2.",
        "flips20": "L’option en tête change pour : {flips}.", "breakeven": "Point de bascule : multiplicateur d’un poids "
        "qui fait gagner la deuxième option", "multiplier": "Multiplicateur", "runner": "Deuxième option",
        "margin": "Avance", "dissent": "Avis divergent", "conditions": "Conditions d’acceptation",
        "risks_sel": "Risques de l’option retenue", "recommendation": "Recommandation", "condition": "Condition",
        "due": "Échéance", "fallback": "Solution de repli", "posthoc": "Les poids ont été modifiés après la notation.",
        "by_gate": "Compromis par jalon de revue", "question": "Décision à prendre",
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
        _add_table(doc, [t["id"], t["trade"], t["level"], t["gate"], t["seat"], t["winner"], t["decision"], t["status"]],
                   [[it["id"], (it.get("state") or {}).get("title", ""),
                     t["levels"].get((it.get("state") or {}).get("level") or "", (it.get("state") or {}).get("level") or "—"),
                     ((it.get("state") or {}).get("gate") or "—").upper(), (it.get("state") or {}).get("seat", ""),
                     (it.get("evaluation") or {}).get("winner") or "",
                     ((it.get("state") or {}).get("decision") or {}).get("selected") or "",
                     t.get((it.get("state") or {}).get("status", "open"), "")] for it in items])

    for n, it in enumerate(items, 2):
        st, ev = it.get("state") or {}, it.get("evaluation") or {}
        _add_section(doc, str(n), f"{it['id']} {st.get('title', '')}".strip())
        absolute = st.get("method") == "absolute_scale"
        lvl = t["levels"].get(st.get("level") or "", st.get("level") or "—")
        meta = [[t["seat"], st.get("seat") or "—"],
                [t["level"], lvl + (f" ({st['level_detail']})" if st.get("level_detail") else "")],
                [t["gate"], (st.get("gate") or "—").upper()],
                [t["scoring"], t["absolute"] if absolute else t["pugh"]],
                [t["method"], t["pairwise"] if ev.get("weights_source") == "pairwise" else t["direct"]]]
        if st.get("decision_question"):
            meta.insert(0, [t["question"], st["decision_question"]])
        _add_table(doc, ["", ""], meta)
        if st.get("must"):
            doc.add_paragraph(f"{t['must']}: " + "; ".join(st["must"]))

        _add_section(doc, f"{n}.1", t["criteria"])
        w = ev.get("weights") or {}
        thr = st.get("thresholds") or {}
        cm = st.get("criteria_meta") or {}
        if absolute or cm:
            _add_table(doc, [t["criterion"], t["weight"], t["source"], t["scale"]],
                       [[c, f"{100 * w.get(c, 0):.0f} %", ", ".join((cm.get(c) or {}).get("source") or []) or "—",
                         (cm.get(c) or {}).get("scale") or "—"] for c in st.get("criteria") or []])
        else:
            _add_table(doc, [t["criterion"], t["weight"], t["threshold"]],
                       [[c, f"{100 * w.get(c, 0):.0f} %", f"{thr[c]:+g}" if c in thr else "—"] for c in st.get("criteria") or []])
        if st.get("post_hoc_weights"):
            doc.add_paragraph(t["posthoc"])

        _add_section(doc, f"{n}.2", t["scores"])
        crit = st.get("criteria") or []
        totals = {x["option"]: x for x in ev.get("totals") or []}
        rows = []
        for o in st.get("options") or []:
            tot = totals.get(o) or {}
            sc = (st.get("scores") or {}).get(o) or {}
            label = f"{o} ({t['datum']})" if tot.get("datum") else o
            if (st.get("option_labels") or {}).get(o):
                label += f": {st['option_labels'][o]}"
            if tot.get("screened"):
                label += f" [{t['screened']}]"
            if tot.get("below_threshold"):
                label += f" [{t['below']}: {', '.join(tot['below_threshold'])}]"
            if absolute:
                rows.append([label, *[f"{sc.get(c, 0):g}" for c in crit], f"{tot.get('weighted', 0):.2f}"])
            else:
                rows.append([label, *[("0" if tot.get("datum") else f"{sc.get(c, 0):+g}") for c in crit],
                             f"{tot.get('weighted', 0):+.2f}", f"{tot.get('unweighted', 0):+g}"])
        _add_table(doc, [t["option"], *crit, t["total"]] + ([] if absolute else [t["unweighted"]]), rows)
        if st.get("screened"):
            _add_table(doc, [t["screened_h"], t["reason"]], [[o, r] for o, r in st["screened"].items()])

        _add_section(doc, f"{n}.3", t["sens"], t["robust"] if ev.get("robust") else t["not_robust"])
        srows = []
        for s in ev.get("sensitivity") or []:
            f = s.get("flip")
            srows.append([s["criterion"], f"{100 * s['weight']:.0f} %",
                          (_pts(f["delta"]) + " pts") if f else "—", (f or {}).get("new_winner") or "—"])
        if srows and not absolute:
            _add_table(doc, [t["criterion"], t["weight"], t["change"], t["new"]], srows)
        if ev.get("sensitivity_pm20"):
            doc.add_paragraph(t["pm20"] + ". " + (t["robust20"] if ev.get("robust_pm20")
                                                  else t["flips20"].format(flips=", ".join(ev.get("flips_at") or []))))
            if ev.get("runner_up"):
                doc.add_paragraph(f"{t['runner']}: {ev['runner_up']}; {t['margin']}: {ev.get('margin', 0):.2f}")
            _add_table(doc, [t["criterion"], t["factor"], t["winner"], t["total"], t["lead"]],
                       [[r["criterion"], f"×{r['factor']:g}".replace(".", "," if lang == "fr" else "."), r["winner"],
                         f"{r['winner_total']:.3f}", f"{r['margin_to_next']:.3f}" if r.get("margin_to_next") is not None else "—"]
                        for r in ev["sensitivity_pm20"]])
            if ev.get("break_even"):
                _add_table(doc, [t["breakeven"], t["multiplier"]],
                           [[b["criterion"], f"×{b['multiplier']:g}"] for b in ev["break_even"]])

        _add_section(doc, f"{n}.4", t["dec"])
        dec = st.get("decision") or {}
        drows = [[t["selected"], dec.get("selected") or "—"], [t["rationale"], dec.get("rationale") or "—"],
                 [t["record"], dec.get("record_id") or (st.get("links") or {}).get("decision_record") or "—"]]
        for key in ("condition", "due", "fallback"):
            if dec.get(key):
                drows.append([t[key], dec[key]])
        if dec.get("risks"):
            drows.append([t["risks"], ", ".join(dec["risks"])])
        _add_table(doc, ["", ""], drows)
        for key, lab in (("recommendation", "recommendation"), ("dissent", "dissent")):
            if st.get(key):
                doc.add_paragraph(f"{t[lab]}: {st[key]}")
        for key, lab in (("acceptance_conditions", "conditions"), ("risks_of_selected", "risks_sel")):
            if st.get(key):
                doc.add_paragraph(f"{t[lab]}: " + "; ".join(st[key]))
        if ev.get("decision_differs_from_winner"):
            doc.add_paragraph(t["differs"])
        for key in ("evidence", "note"):
            if st.get(key):
                doc.add_paragraph(f"{t[key]}: {st[key]}")
        if st.get("evidence_by_criterion"):
            _add_table(doc, [t["criterion"], t["evidence"]], [[c, v] for c, v in st["evidence_by_criterion"].items()])

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
