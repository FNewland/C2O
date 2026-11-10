"""SpaceCDF Word document family: semp. Systems Engineering Management Plan (SEMP).

Moved verbatim from services/docx_generator.py in W0.1. Wave 3 (3.X3): ``generate_semp_from_export``
builds the SEMP from the study (organisation and seats, life cycle and baselines, technical
processes with their evidence, model philosophy, validation, schedule, risk, configuration
management, tailoring, the systems-engineering figures), EN or FR; ``generate_semp_docx`` stays for
calls without a study.
See design/docs/dev/W0_SEAMS.md for ownership.
"""
from __future__ import annotations

import io
from typing import Any

from docx import Document

from ._common import (
    _add_cover_page,
    _render_bullet,
    _add_diagrams,
    _add_footer,
    _add_section,
    _add_table,
    _add_toc_placeholder,
    _setup_margins,
    _setup_styles,
)


def generate_semp_docx(study_name: str, data: dict[str, Any]) -> bytes:
    """Generate Systems Engineering Management Plan (NASA SEH Appendix J)."""
    doc = Document()
    _setup_styles(doc)
    _setup_margins(doc)

    _add_cover_page(doc, "Systems Engineering Management Plan", "NASA SEH Appendix J / ECSS-M-ST-10C", study_name)
    _add_toc_placeholder(doc)
    _add_footer(doc, study_name)

    _add_section(doc, "1", "Introduction")
    _add_section(doc, "1.1", "Purpose", "This SEMP defines the systems engineering approach, processes, and management controls.")
    _add_section(doc, "1.2", "Mission Overview")
    mission_need = data.get("mission_need", {})
    doc.add_paragraph(mission_need.get("problem_statement", "To be defined"))

    _add_section(doc, "2", "SE Organisation and Responsibilities")
    doc.add_paragraph("The SE team follows the CDF concurrent engineering model with 16 specialist positions.")
    _add_table(doc, ["Role", "Responsibility"],
               [["Systems Engineer", "Technical baseline, budgets, trade studies"],
                ["Mission Analyst", "Orbit, coverage, delta-V analysis"],
                ["Payload Lead", "Instrument performance, data products"],
                ["Power Engineer", "EPS sizing, energy balance"],
                ["AOCS Engineer", "Pointing, orbit maintenance"],
                ["Comms Engineer", "Link budget, TTC design"],
                ["Thermal Engineer", "Thermal control, analysis"],
                ["Structures Engineer", "Configuration, mass budget, AIT"]])

    _add_section(doc, "3", "Technical Processes")
    _add_section(doc, "3.1", "Requirements Engineering", "Suggest-then-approve pattern with SMART validation. Requirements linked to functions and traced to objectives.")
    _add_section(doc, "3.2", "Architecture Design", "Trade studies per subsystem with derived requirements. Options evaluated on mass, power, cost, TRL.")
    _add_section(doc, "3.3", "Interface Management", "Interfaces captured at segment and subsystem level. Managed via interface matrix.")
    _add_section(doc, "3.4", "Verification & Validation", "V&V matrix per ECSS-E-ST-10-02C. Methods: Analysis, Test, Inspection, Demonstration.")

    _add_section(doc, "4", "Technical Management Processes")
    _add_section(doc, "4.1", "Configuration Management", "Design baselines at SRR, PDR, CDR. Change control via board.")
    _add_section(doc, "4.2", "Risk Management", "5x5 risk matrix per ECSS-M-ST-80C. Continuous monitoring.")
    _add_section(doc, "4.3", "Technical Budgets", "Mass, power, link, pointing, delta-V, data, cost. Margins per ECSS design phase.")

    _add_section(doc, "5", "Reviews and Decision Gates")
    _add_table(doc, ["Review", "Phase Entry", "Key Deliverables"],
               [["MDR", "0 \u2192 A", "Mission Need Statement, ConOps outline"],
                ["PRR", "A \u2192 B", "Preliminary requirements, product and function trees, budgets with margins"],
                ["SRR", "B", "Requirements baseline, functional architecture"],
                ["PDR", "B \u2192 C", "Preliminary design, budgets with margin"],
                ["CDR", "C \u2192 D", "Detailed design, manufacturing drawings, test plan"],
                ["TRR", "D (test)", "Qualified hardware, test procedures"],
                ["FRR", "D (launch)", "Flight-ready spacecraft, ops procedures"]])

    _add_diagrams(doc, "6", "System Diagrams", data,
                  "Operations concept, architecture, interfaces, requirements and risk figures drawn from the design "
                  "model (the same figures as the SpaceCDF Diagrams view). The gate and maturity each figure is "
                  "expected at follow its caption (D draft, B baselined, U updated).")

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Wave 3 (3.X3): the SEMP generated from the study (reviewable at SRR)
# ---------------------------------------------------------------------------

_S = {
    "title": ("Systems Engineering Management Plan", "Plan de management de l’ingénierie système"),
    "std": ("ECSS-E-ST-10C Annex D (SEP) / NASA SEH Appendix J", "ECSS-E-ST-10C annexe D (SEP) / NASA SEH annexe J"),
    "intro": ("Introduction", "Introduction"),
    "purpose": ("Purpose and scope", "Objet et domaine d’application"),
    "purpose_txt": ("This plan states how the {name} team runs systems engineering: who owns what, which reviews the "
                    "project passes, which technical processes produce which evidence, how the design is verified and "
                    "validated, and how baselines and changes are controlled. It is generated from the study, so it "
                    "describes what the team actually holds; sections that the study cannot yet fill say so.",
                    "Ce plan décrit comment l’équipe {name} conduit l’ingénierie système : qui est responsable de quoi, "
                    "quelles revues le projet franchit, quels processus techniques produisent quelles preuves, comment la "
                    "conception est vérifiée et validée, et comment les références et les modifications sont maîtrisées. "
                    "Il est généré à partir de l’étude : il décrit ce que l’équipe détient réellement ; les sections que "
                    "l’étude ne peut pas encore remplir le disent."),
    "mission": ("Mission overview", "Présentation de la mission"),
    "org": ("Organisation and seats", "Organisation et postes"),
    "org_txt": ("The team works in seats (concurrent design facility). Each seat owns parameters and elements; a change "
                "to another seat's parameter is a proposal that seat accepts or rejects.",
                "L’équipe travaille par postes (installation de conception concourante). Chaque poste est responsable de "
                "paramètres et d’éléments ; modifier le paramètre d’un autre poste est une proposition que ce poste accepte "
                "ou refuse."),
    "life": ("Life cycle, reviews and baselines", "Cycle de vie, revues et références"),
    "proc": ("Technical processes", "Processus techniques"),
    "model": ("Model philosophy and verification approach", "Philosophie des modèles et approche de vérification"),
    "val": ("Validation approach", "Approche de validation"),
    "sched": ("Schedule and milestones", "Calendrier et jalons"),
    "risk": ("Risk management", "Gestion des risques"),
    "cm": ("Configuration management", "Gestion de configuration"),
    "tailor": ("Tailoring", "Adaptation"),
    "figs": ("Systems-engineering figures", "Figures d’ingénierie système"),
    "figs_txt": ("The figures are drawn from the design model (same as the Diagrams tab). Each lists what the model "
                 "still lacks for it.", "Les figures sont tirées du modèle de conception (comme l’onglet Diagrammes). "
                 "Chacune liste ce qui manque encore au modèle."),
    "none": ("Not yet recorded in the study.", "Pas encore enregistré dans l’étude."),
}


def _semp_t(key: str, lang: str, **kw: Any) -> str:
    en, fr = _S[key]
    return (fr if lang == "fr" else en).format(**kw)


def _pick(v: Any, lang: str) -> str:
    if isinstance(v, dict):
        return str(v.get(lang) or v.get("en") or "")
    return "" if v is None else str(v)


def _sec(sx: Any, name: str) -> dict:
    s = getattr(sx, name, None) or {}
    return s if isinstance(s, dict) else {}


def _items(s: dict, key: str = "items") -> list[dict]:
    if s.get("status") == "not_implemented":
        return []
    return [x for x in (s.get(key) or []) if isinstance(x, dict)]


def _evidence(sx: Any, path: str) -> str:
    sec, _, key = path.partition(".")
    s = _sec(sx, sec)
    if s.get("status") == "not_implemented":
        return "—"
    v = s.get(key)
    return str(len(v)) if isinstance(v, list) else "—"


def generate_semp_from_export(sx: Any, lang: str = "en", diagrams: list[dict] | None = None) -> bytes:
    """The SEMP of a collected study (``StudyExport`` with every section)."""
    from ._common import _add_footer as add_footer
    lang = "fr" if str(lang or "").lower().startswith("fr") else "en"
    fr = lang == "fr"
    T = lambda k, **kw: _semp_t(k, lang, **kw)  # noqa: E731
    name = getattr(sx, "study_name", "") or ""
    semp = _sec(sx, "semp")
    doc = Document()
    _setup_styles(doc)
    _setup_margins(doc)
    _add_cover_page(doc, T("title"), T("std"), name)
    _add_toc_placeholder(doc)
    add_footer(doc, name, "SEMP")

    _add_section(doc, "1", T("intro"))
    _add_section(doc, "1.1", T("purpose"), T("purpose_txt", name=name))
    need = _sec(sx, "need")
    _add_section(doc, "1.2", T("mission"), need.get("problem_statement") or T("none"))
    if need.get("conops_summary"):
        doc.add_paragraph(need["conops_summary"])
    objs = [o for o in need.get("objectives") or [] if isinstance(o, dict)]
    if objs:
        _add_table(doc, ["ID", "Objectif" if fr else "Objective", "Priorité" if fr else "Priority"],
                   [[o.get("id") or "", o.get("text") or "", o.get("priority") or ""] for o in objs])

    # 2 organisation
    _add_section(doc, "2", T("org"), T("org_txt"))
    org = semp.get("organisation") or []
    if org:
        _add_table(doc, ["Poste" if fr else "Seat", "Nature" if fr else "Kind", "Paramètres" if fr else "Parameters",
                         "Éléments" if fr else "Elements", "Exigences" if fr else "Requirements"],
                   [[_pick(o.get("label"), lang), o.get("kind") or "", ", ".join(o.get("owns_parameters") or []),
                     ", ".join(o.get("elements") or []) or ", ".join(o.get("owns_domains") or []), str(o.get("requirements") or 0)]
                    for o in org])
    else:
        doc.add_paragraph(T("none"))
    sh = _items(_sec(sx, "stakeholders"))
    if sh:
        _add_section(doc, "2.1", "Parties prenantes et autorité de décision" if fr else "Stakeholders and decision authority")
        _add_table(doc, ["ID", "Nom" if fr else "Name", "Catégorie" if fr else "Category", "Engagement"],
                   [[s.get("code") or s.get("id") or "", s.get("name") or "", str(s.get("category") or "").replace("_", " "),
                     s.get("engagement") or ""] for s in sh])

    # 3 life cycle
    _add_section(doc, "3", T("life"))
    life = semp.get("lifecycle") or []
    if life:
        _add_table(doc, ["Revue" if fr else "Review", "Phase", "Référence" if fr else "Baseline", "État" if fr else "State",
                         "Produits référencés" if fr else "Products baselined"],
                   [[g.get("short") or "", g.get("phase") or "", _pick(g.get("baseline"), lang), g.get("state") or "",
                     "; ".join(_pick(p, lang) for p in g.get("products_baselined") or [])] for g in life])
    else:
        doc.add_paragraph(T("none"))

    # 4 technical processes
    _add_section(doc, "4", T("proc"))
    procs = semp.get("processes") or []
    for i, p in enumerate(procs, 1):
        _add_section(doc, f"4.{i}", _pick(p.get("label"), lang), _pick(p.get("how"), lang))
        ev = [(k, _evidence(sx, k)) for k in (p.get("evidence") or {})]
        if ev:
            doc.add_paragraph(("Preuves dans l’étude : " if fr else "Evidence in the study: ")
                              + "; ".join(f"{k} = {v}" for k, v in ev) + f" ({p.get('standard') or ''})")

    # 5 model philosophy and verification
    _add_section(doc, "5", T("model"))
    ait = _sec(sx, "ait")
    models = _items(ait, "models")
    if models:
        doc.add_paragraph(("Philosophie : " if fr else "Philosophy: ") + str(ait.get("philosophy") or "—"))
        _add_table(doc, ["ID", "Modèle" if fr else "Model", "Niveau" if fr else "Level", "Objet" if fr else "Purpose"],
                   [[m.get("code") or m.get("id") or "", (m.get("name_fr") if fr else None) or m.get("name") or "",
                     m.get("level") or "", (m.get("purpose_fr") if fr else None) or m.get("purpose") or ""] for m in models])
    else:
        doc.add_paragraph(T("none"))
    reqs = [r for r in (_sec(sx, "requirements").get("items") or []) if not r.get("generated_interface")
            and r.get("level") != "stakeholder" and not str(r.get("code") or "").startswith(("OBJ-", "SN-", "IR-"))]
    by_stage: dict[str, int] = {}
    by_method: dict[str, int] = {}
    for r in reqs:
        by_stage[str(r.get("verification_phase") or "—")] = by_stage.get(str(r.get("verification_phase") or "—"), 0) + 1
        by_method[str(r.get("verification_method") or "—")] = by_method.get(str(r.get("verification_method") or "—"), 0) + 1
    if reqs:
        doc.add_paragraph(("Exigences par étape de clôture : " if fr else "Requirements by closing stage: ")
                          + ", ".join(f"{k} {v}" for k, v in sorted(by_stage.items())))
        doc.add_paragraph(("Exigences par méthode : " if fr else "Requirements by method: ")
                          + ", ".join(f"{k} {v}" for k, v in sorted(by_method.items())))

    # 6 validation
    _add_section(doc, "6", T("val"))
    acts = _items(_sec(sx, "validation"))
    if acts:
        _add_table(doc, ["ID", "Activité" if fr else "Activity", "Quand" if fr else "When", "Par" if fr else "By"],
                   [[a.get("code") or "", a.get("title") or "", a.get("stage") or "", a.get("performer") or ""] for a in acts])
    else:
        doc.add_paragraph(T("none"))

    # 7 schedule
    _add_section(doc, "7", T("sched"))
    sch = _sec(sx, "schedule")
    ms = _items(sch, "milestones")
    if ms:
        _add_table(doc, ["Jalon" if fr else "Milestone", "Date", "État" if fr else "Status"],
                   [[m.get("name") or m.get("id") or "", m.get("date") or m.get("due") or "", m.get("status") or ""] for m in ms])
    else:
        doc.add_paragraph(T("none"))

    # 8 risk
    _add_section(doc, "8", T("risk"))
    risks = _items(_sec(sx, "risks"))
    if risks:
        top = sorted(risks, key=lambda r: -(r.get("score") or 0))[:10]
        doc.add_paragraph((f"{len(risks)} risques au registre ; les dix plus élevés :" if fr else
                           f"{len(risks)} risks in the register; the ten highest:"))
        _add_table(doc, ["ID", "Risque" if fr else "Risk", "P×G" if fr else "L×C", "Résiduel" if fr else "Residual",
                         "Responsable" if fr else "Owner"],
                   [[r.get("id") or "", (r.get("description") or "")[:140], str(r.get("score") or ""),
                     str(r.get("residual_rpn") or (f"{r.get('residual_likelihood')}×{r.get('residual_consequence')}"
                                                   if r.get("residual_likelihood") else "")),
                     r.get("owner_seat") or r.get("owner") or ""] for r in top])
    else:
        doc.add_paragraph(T("none"))

    # 9 configuration management
    _add_section(doc, "9", T("cm"))
    cm = semp.get("configuration_management") or {}
    if cm.get("change_rule"):
        doc.add_paragraph(_pick(cm["change_rule"], lang))
    for c in cm.get("change_classes") or []:
        _render_bullet(doc, "- " + _pick(c.get("label"), lang))
    if cm.get("baselines"):
        _add_table(doc, ["Jalon" if fr else "Gate", "Référence" if fr else "Baseline", "Le" if fr else "Passed at"],
                   [[str(b.get("gate") or "").upper(), _pick(b.get("baseline"), lang), str(b.get("passed_at") or "")[:19]]
                    for b in cm["baselines"]])
    ch = _items(_sec(sx, "changes"))
    if ch:
        _add_table(doc, ["ID", "Titre" if fr else "Title", "Classe" if fr else "Class", "État" if fr else "Status"],
                   [[x.get("code") or "", x.get("title") or "", x.get("change_class") or "", x.get("status") or ""] for x in ch])
    icds = _items(_sec(sx, "icds"))
    if icds:
        doc.add_paragraph((f"{len(icds)} ICD sous contrôle d’édition." if fr else f"{len(icds)} ICDs under issue control."))

    # 10 tailoring
    _add_section(doc, "10", T("tailor"))
    tl = semp.get("tailoring") or []
    if tl:
        _add_table(doc, ["Élément" if fr else "Item", "Choix" if fr else "Choice", "Justification" if fr else "Rationale"],
                   [[_pick(x.get("label"), lang), _pick(x.get("value"), lang), _pick(x.get("rationale"), lang)] for x in tl])
    else:
        doc.add_paragraph(T("none"))

    # 11 figures
    if diagrams:
        from ..diagrams.render import add_diagram
        _add_section(doc, "11", T("figs"), T("figs_txt"))
        for m in diagrams:
            add_diagram(doc, m, lang=lang, heading_level=2, gaps=True, table=False)

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
