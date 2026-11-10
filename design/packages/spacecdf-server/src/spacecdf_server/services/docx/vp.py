"""SpaceCDF Word document family: vp. Verification Plan (VP).

W1.09a: the matrix lists every requirement the team entered (no row cap), by level then code,
with the method and stage stored on the requirement and the status of its verification item.
Owned by agent A after W1.09a (W8a model philosophy and AIT programme).
See design/docs/dev/W0_SEAMS.md for ownership.
"""
from __future__ import annotations

import io
from typing import Any

from docx import Document

from ._common import (
    _add_cover_page,
    _add_footer,
    _add_section,
    _add_table,
    _add_toc_placeholder,
    _setup_margins,
    _setup_styles,
)


def generate_vp_docx(
    study_name: str = "",
    requirements: list[dict[str, Any]] | None = None,
    verification_items: list[dict[str, Any]] | None = None,
) -> bytes:
    """Generate Verification Plan as .docx bytes."""
    doc = Document()
    _setup_styles(doc)
    _setup_margins(doc)
    reqs = [r for r in (requirements or []) if not str(r.get("code") or "").startswith("IR-")]
    vi = {v.get("requirement_id"): v for v in (verification_items or [])}

    _add_cover_page(doc, "Verification Plan", "ECSS-E-ST-10-02C Rev.1", study_name)
    _add_toc_placeholder(doc)
    _add_footer(doc, study_name)

    _add_section(doc, "1", "Introduction")
    _add_section(doc, "1.1", "Purpose", f"Defines the verification approach for {study_name}.")
    _add_section(doc, "1.2", "Verification Methods",
                 "Analysis (A), Test (T), Review of Design (R), Inspection (I) per ECSS-E-ST-10-02C.")

    _add_section(doc, "2", "Verification Matrix")
    if reqs:
        doc.add_paragraph(f"{len(reqs)} requirements, by level then code.")
        _add_table(doc,
                   ["Code", "Level", "Requirement", "Method", "Stage", "Level of verification", "Status"],
                   [[r.get("code") or r.get("id", ""), r.get("level") or "", r.get("text") or "",
                     (vi.get(r.get("id")) or {}).get("method") or r.get("verification_method") or "",
                     r.get("verification_phase") or (vi.get(r.get("id")) or {}).get("phase") or "",
                     (vi.get(r.get("id")) or {}).get("level") or "",
                     (vi.get(r.get("id")) or {}).get("status") or "no verification item"] for r in reqs])
    else:
        doc.add_paragraph("No requirements have been entered for this study.")

    _add_section(doc, "3", "Environmental Test Programme")
    _add_section(doc, "3.1", "Vibration", "Sine + random per launch vehicle PUG. 3 axes, 1 min/axis.")
    _add_section(doc, "3.2", "Thermal Vacuum", "Qualification range +/-10C beyond operating. 4 cycles minimum.")
    _add_section(doc, "3.3", "EMC", "Per ECSS-E-ST-20-07C if required by launch provider.")

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


# ═════════════════════════════════════════════════════════════════════════════
# W8a: the verification plan from the study (owner A). Takes a StudyExport, so its numbers are
# those of the workbench: the ``ait`` section (model philosophy, test matrix, environment levels,
# verification items by stage) and the ``schedule`` section (model and review dates).
# ═════════════════════════════════════════════════════════════════════════════

_VP_TEXT: dict[str, dict[str, str]] = {
    "title": {"en": "Verification Plan", "fr": "Plan de vérification"},
    "standard": {"en": "ECSS-E-ST-10-02C Rev.1 (verification), ECSS-E-ST-10-03C (testing)",
                 "fr": "ECSS-E-ST-10-02C Rev.1 (vérification), ECSS-E-ST-10-03C (essais)"},
    "intro": {"en": "Introduction", "fr": "Introduction"},
    "purpose": {"en": "This plan defines how every requirement of {name} is verified: the model philosophy, the "
                      "test matrix, the environmental test levels and, for each close-out stage, the verification "
                      "items with their method, level and facility. Generated from the study model.",
                "fr": "Ce plan définit comment chaque exigence de {name} est vérifiée : la philosophie des modèles, "
                      "la matrice d’essais, les niveaux d’essais d’environnement et, pour chaque étape de clôture, "
                      "les éléments de vérification avec leur méthode, leur niveau et leur moyen. Généré à partir "
                      "du modèle de l’étude."},
    "models": {"en": "Model philosophy", "fr": "Philosophie des modèles"},
    "philosophy": {"en": "Philosophy: {p}. {n} models.", "fr": "Philosophie : {p}. {n} modèles."},
    "model": {"en": "Model", "fr": "Modèle"}, "level": {"en": "Level", "fr": "Niveau"},
    "due": {"en": "Due", "fr": "Échéance"}, "purpose_h": {"en": "Purpose", "fr": "Objet"},
    "month": {"en": "month {m}", "fr": "mois {m}"},
    "approach": {"en": "Verification approach", "fr": "Démarche de vérification"},
    "methods": {"en": "Methods", "fr": "Méthodes"}, "stages": {"en": "Close-out stages", "fr": "Étapes de clôture"},
    "levels": {"en": "Verification levels", "fr": "Niveaux de vérification"},
    "count": {"en": "Items", "fr": "Éléments"}, "method": {"en": "Method", "fr": "Méthode"},
    "stage": {"en": "Stage", "fr": "Étape"},
    "matrix": {"en": "Test matrix", "fr": "Matrice d’essais"},
    "test": {"en": "Test", "fr": "Essai"}, "category": {"en": "Category", "fr": "Catégorie"},
    "source": {"en": "Level source", "fr": "Source des niveaux"}, "facility": {"en": "Facility", "fr": "Moyen"},
    "verifies": {"en": "Verifies", "fr": "Vérifie"},
    "env": {"en": "Environmental test levels", "fr": "Niveaux des essais d’environnement"},
    "launch": {"en": "Launch", "fr": "Lancement"}, "parameter": {"en": "Parameter", "fr": "Paramètre"},
    "value": {"en": "Value", "fr": "Valeur"},
    "items": {"en": "Verification items by stage", "fr": "Éléments de vérification par étape"},
    "code": {"en": "Code", "fr": "Code"}, "requirement": {"en": "Requirement", "fr": "Exigence"},
    "tests": {"en": "Tests", "fr": "Essais"},
    "none": {"en": "No item closes at this stage.", "fr": "Aucun élément ne se clôt à cette étape."},
    "open": {"en": "Open items", "fr": "Points ouverts"},
    "proposed": {"en": "The model philosophy and test matrix shown are the default proposal: the study has not "
                       "stored its own yet (AIT panel, Propose).",
                 "fr": "La philosophie des modèles et la matrice d’essais présentées sont la proposition par "
                       "défaut : l’étude n’a pas encore enregistré les siennes (panneau AIT, Proposer)."},
    "unassigned": {"en": "{n} requirement(s) have no close-out stage.",
                   "fr": "{n} exigence(s) n’ont pas d’étape de clôture."},
    "unlinked": {"en": "Tests that verify no requirement yet: {codes}.",
                 "fr": "Essais qui ne vérifient encore aucune exigence : {codes}."},
    "no_open": {"en": "None.", "fr": "Aucun."},
}

_ENV_NAMES = {
    "qs": {"en": "Quasi-static (axial / lateral)", "fr": "Quasi-statique (axial / latéral)"},
    "sine": {"en": "Sine", "fr": "Sinus"}, "random": {"en": "Random", "fr": "Aléatoire"},
    "tvac": {"en": "Thermal vacuum", "fr": "Vide thermique"},
}
_STAGE_NAMES = {
    "PDR": {"en": "Preliminary design review (PDR)", "fr": "Revue de conception préliminaire (PDR)"},
    "CDR": {"en": "Critical design review (CDR)", "fr": "Revue critique de conception (CDR)"},
    "QR": {"en": "Qualification review (QR)", "fr": "Revue de qualification (QR)"},
    "AR": {"en": "Acceptance review (AR)", "fr": "Revue de recette (AR)"},
    "IOV": {"en": "In-orbit verification (IOV)", "fr": "Vérification en orbite (IOV)"},
    "unassigned": {"en": "No stage yet", "fr": "Sans étape"},
}
_METHOD_NAMES = {"T": {"en": "Test", "fr": "Essai"}, "A": {"en": "Analysis", "fr": "Analyse"},
                 "R": {"en": "Review of design", "fr": "Revue de conception"},
                 "I": {"en": "Inspection", "fr": "Inspection"}, "?": {"en": "not set", "fr": "non définie"}}


def _num_fr(v: Any, lang: str) -> str:
    s = f"{v:g}" if isinstance(v, float) else str(v)
    return s.replace(".", ",") if lang == "fr" else s


def generate_verification_plan_docx(sx: Any, lang: str = "en") -> bytes:
    """The verification plan (W8a) of a collected study (``export_context.StudyExport``)."""
    lang = "fr" if str(lang or "").lower().startswith("fr") else "en"

    def T(key: str, **kw: Any) -> str:
        return _VP_TEXT[key][lang].format(**kw)

    ait = getattr(sx, "ait", None) or {}
    sched = getattr(sx, "schedule", None) or {}
    name = getattr(sx, "study_name", "") or ""
    models = ait.get("models") or []
    tests = ait.get("tests") or []
    items = ait.get("items") or []
    counts = ait.get("counts") or {}
    env = ait.get("environment") or {}
    model_dates = {m.get("code"): m.get("date") for m in sched.get("milestones") or [] if m.get("kind") == "model"}

    doc = Document()
    _setup_styles(doc)
    _setup_margins(doc)
    _add_cover_page(doc, T("title"), T("standard"), name)
    _add_toc_placeholder(doc)
    _add_footer(doc, name, "VP")

    _add_section(doc, "1", T("intro"), T("purpose", name=name))
    if ait.get("status") == "proposed":
        doc.add_paragraph(T("proposed"))

    # 2 model philosophy
    _add_section(doc, "2", T("models"), T("philosophy", p=ait.get("philosophy") or "—", n=len(models)))
    _add_table(doc, [T("model"), T("level"), T("due"), T("purpose_h")], [
        [f"{m.get('code')}: {(m.get('name_fr') if lang == 'fr' else m.get('name')) or m.get('name') or ''}",
         str(m.get("level") or ""),
         " · ".join(x for x in (T("month", m=m["due_month"]) if m.get("due_month") is not None else "",
                                model_dates.get(m.get("code")) or "") if x),
         (m.get("purpose_fr") if lang == "fr" else m.get("purpose")) or m.get("purpose") or ""]
        for m in models])

    # 3 approach
    _add_section(doc, "3", T("approach"))
    _add_section(doc, "3.1", T("methods"))
    _add_table(doc, [T("method"), T("count")],
               [[f"{k} — {_METHOD_NAMES.get(k, {}).get(lang, k)}", str(v)]
                for k, v in sorted((counts.get("by_method") or {}).items())])
    _add_section(doc, "3.2", T("stages"))
    _add_table(doc, [T("stage"), T("count")],
               [[_STAGE_NAMES.get(k, {}).get(lang, k), str(v)] for k, v in (counts.get("by_stage") or {}).items()])
    _add_section(doc, "3.3", T("levels"))
    _add_table(doc, [T("level"), T("count")], [[k, str(v)] for k, v in sorted((counts.get("by_level") or {}).items())])

    # 4 test matrix: test x model x level
    codes = [m.get("code") for m in models]
    _add_section(doc, "4", T("matrix"))
    _add_table(doc, [T("test"), T("category"), *codes, T("level"), T("stage"), T("source"), T("facility"), T("verifies")], [
        [f"{t.get('code')}: {(t.get('name_fr') if lang == 'fr' else t.get('name')) or t.get('name') or ''}",
         str(t.get("category") or ""),
         *["X" if c in (t.get("models") or []) else "" for c in codes],
         str(t.get("level") or ""), str(t.get("stage") or ""), str(t.get("level_source") or ""),
         str(t.get("facility") or ""), ", ".join(t.get("requirement_codes") or []) or "—"]
        for t in tests])

    # 5 environment levels (from the launch segment)
    _add_section(doc, "5", T("env"), f"{T('launch')}: {env.get('launch') or '—'}. {T('source')}: "
                                     f"{env.get('level_source') or '—'}. {env.get('philosophy') or ''}")
    rows: list[list[str]] = []
    qs = env.get("quasi_static") or {}
    if qs.get("axial_g") is not None:
        rows.append([_ENV_NAMES["qs"][lang], f"{_num_fr(qs['axial_g'], lang)} g / {_num_fr(qs['lateral_g'], lang)} g"])
    sine, rnd, tv = env.get("sine") or {}, env.get("random") or {}, env.get("tvac") or {}
    if sine:
        rows.append([_ENV_NAMES["sine"][lang], f"{_num_fr(sine.get('level_g'), lang)} g, {sine.get('range_hz', ['', ''])[0]}–"
                             f"{sine.get('range_hz', ['', ''])[1]} Hz, {sine.get('axes')} axes. {sine.get('note', '')}"])
    if rnd:
        rows.append([_ENV_NAMES["random"][lang], f"{_num_fr(rnd.get('grms'), lang)} grms, {rnd.get('range_hz', ['', ''])[0]}–"
                               f"{rnd.get('range_hz', ['', ''])[1]} Hz, {rnd.get('duration_s_per_axis')} s/axis. "
                               f"{rnd.get('note', '')}"])
    if tv:
        rows.append([_ENV_NAMES["tvac"][lang], f"{tv.get('cycles')} cycles, ≤ {tv.get('pressure_hpa')} hPa, "
                                       f"± {tv.get('margin_c')} °C. {tv.get('note', '')}"])
    if rows:
        _add_table(doc, [T("parameter"), T("value")], rows)

    # 6 verification items by stage (every item, no cap)
    _add_section(doc, "6", T("items"))
    order = ["PDR", "CDR", "QR", "AR", "IOV", "unassigned"]
    for k, st in enumerate([s for s in order if s != "unassigned" or (counts.get("by_stage") or {}).get(s)], 1):
        rows_st = [i for i in items if i.get("stage") == st]
        _add_section(doc, f"6.{k}", f"{_STAGE_NAMES[st][lang]} — {len(rows_st)}")
        if not rows_st:
            doc.add_paragraph(T("none"))
            continue
        _add_table(doc, [T("code"), T("requirement"), T("method"), T("level"), T("facility"), T("tests")], [
            [str(i.get("code") or ""), str(i.get("text") or ""), "+".join(i.get("methods") or []) or "—",
             str(i.get("level") or ""), str(i.get("facility") or ""), ", ".join(i.get("tests") or []) or "—"]
            for i in rows_st])

    # 7 open items
    _add_section(doc, "7", T("open"))
    opened = []
    n_un = (counts.get("by_stage") or {}).get("unassigned", 0)
    if n_un:
        opened.append(T("unassigned", n=n_un))
    unlinked = [t.get("code") for t in tests if not t.get("requirement_codes")]
    if unlinked:
        opened.append(T("unlinked", codes=", ".join(unlinked)))
    for line in opened or [T("no_open")]:
        doc.add_paragraph(line)

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
