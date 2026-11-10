"""SpaceCDF Word document family: ts. Technical requirements specification (TS).

W1.09a: every requirement the team entered (no row cap), with its threshold, verification and
allocation; interface requirements generated from links (``IR-*``) are in the IRD.

W4.06 (ECSS-E-ST-10-06C Annex A): the requirements are grouped by type (functional, performance,
interface, environmental, operational, product assurance, regulatory; ``group_of``) and each row
carries the fields of the W2 requirement model: level, priority, category, threshold and unit,
verification methods, verification level and stage, every parent (``parent_ids``, W2.03),
allocation and rationale. The environment section comes from the orbit (mission section of the
collector), the launch segment and the AIT environment levels (W8a), and quotes the environmental
requirements with their source (for example a dose estimate still to be confirmed by SPENVIS).

``generate_ts_from_export(sx, lang)`` is the generator; ``generate_ts_docx(study_name, data)`` is
the legacy entry of ``/docx/ts`` without a study. Stakeholder needs (level ``stakeholder``) are in
the MRD. See design/docs/dev/W0_SEAMS.md for ownership.
"""
from __future__ import annotations

import io
import json
from typing import Any

from docx import Document

from ._common import (
    _add_cover_page,
    _add_footer,
    _add_section,
    _add_table,
    _add_toc_placeholder,
    _compact_table,
    _orient,
    _setup_margins,
    _setup_styles,
)

LEVEL_ORDER = ("stakeholder", "mission", "segment", "system", "subsystem", "interface")

#: requirement groups of the TS, in document order
GROUPS = ("functional", "performance", "interface", "environmental", "operational", "product_assurance", "regulatory")
GROUP_TITLES = {
    "functional": {"en": "Functional requirements", "fr": "Exigences fonctionnelles"},
    "performance": {"en": "Performance requirements", "fr": "Exigences de performance"},
    "interface": {"en": "Interface requirements", "fr": "Exigences d’interface"},
    "environmental": {"en": "Environmental requirements", "fr": "Exigences d’environnement"},
    "operational": {"en": "Operational requirements", "fr": "Exigences opérationnelles"},
    "product_assurance": {"en": "Product assurance requirements", "fr": "Exigences d’assurance produit"},
    "regulatory": {"en": "Regulatory requirements", "fr": "Exigences réglementaires"},
}
#: categories (W2.02 ``category``) that put a requirement in a group whatever its type
ENV_CATEGORIES = {"environment", "launch", "emc", "radiation", "space_environment"}
PA_CATEGORIES = {"verification", "reliability", "safety", "cleanliness", "quality", "materials", "product_assurance"}
OPS_CATEGORIES = {"operations", "modes_fdir", "autonomy", "ops"}


def group_of(r: dict[str, Any]) -> str:
    """The TS group of a requirement, from its type (``req_type``), category and level."""
    rtype = str(r.get("req_type") or "").lower()
    cat = str(r.get("category") or "").lower()
    if rtype == "regulatory" or cat == "regulatory":
        return "regulatory"
    if rtype == "interface" or cat == "interface" or r.get("level") == "interface":
        return "interface"
    if cat in ENV_CATEGORIES or rtype in ("environmental", "environment"):
        return "environmental"
    if rtype in ("process", "product_assurance") or cat in PA_CATEGORIES:
        return "product_assurance"
    if cat in OPS_CATEGORIES or rtype == "operational":
        return "operational"
    if rtype == "performance":
        return "performance"
    return "functional"


def _num(v: Any) -> str:
    if isinstance(v, float) and v == int(v):
        v = int(v)
    return str(v)


def threshold_value_text(r: dict[str, Any]) -> str:
    """``>= 10`` / ``50 to 70`` / ``before 2029-06-30``: the stored threshold without its unit."""
    val = r.get("threshold_value")
    op = str(r.get("threshold_op") or "")
    if val is None or val == "":
        return "exists" if op == "exists" else ""
    if isinstance(val, str) and val.strip().startswith("{"):
        try:
            val = json.loads(val)
        except ValueError:
            pass
    if isinstance(val, dict) and ("min" in val or "max" in val):
        lo, hi = val.get("min"), val.get("max")
        return f"{_num(lo) if lo is not None else '…'} to {_num(hi) if hi is not None else '…'}"
    if op == "in_range" and isinstance(val, (list, tuple)) and len(val) == 2:
        return f"{_num(val[0])} to {_num(val[1])}"
    return " ".join(p for p in (op, _num(val)) if p).strip()


def threshold_text(r: dict[str, Any]) -> str:
    """``>= 10`` / ``<= 30 s``: the stored threshold of a requirement with its unit ("" when none)."""
    v = threshold_value_text(r)
    if not v:
        return ""
    unit = str(r.get("threshold_unit") or r.get("unit") or "")
    return f"{v} {unit}".strip()


def _methods(r: dict[str, Any]) -> str:
    ms = [m for m in (r.get("verification_methods") or []) if m]
    if not ms and r.get("verification_method"):
        ms = [r["verification_method"]]
    return "/".join(dict.fromkeys(str(m) for m in ms))


def _level_key(r: dict[str, Any]) -> tuple:
    lvl = str(r.get("level") or "")
    return (LEVEL_ORDER.index(lvl) if lvl in LEVEL_ORDER else len(LEVEL_ORDER), str(r.get("code") or ""))


_TXT = {
    "title": {"en": "Technical Requirements Specification", "fr": "Spécification technique des besoins"},
    "intro": {"en": "Introduction", "fr": "Introduction"},
    "purpose_h": {"en": "Purpose", "fr": "Objet"},
    "purpose": {"en": "This specification states the technical requirements of the {name} system and its elements, "
                      "grouped by type, with their verification and their traceability to the parent requirements.",
                "fr": "Cette spécification énonce les exigences techniques du système {name} et de ses éléments, "
                      "regroupées par type, avec leur vérification et leur traçabilité vers les exigences mères."},
    "conv_h": {"en": "Conventions", "fr": "Conventions"},
    "conv": {"en": "Priority: 1 mandatory (the mission or a licence fails without it), 2 needed for full performance, "
                   "3 goal. Verification methods (ECSS-E-ST-10-02C): T test (including demonstration), A analysis, "
                   "R review of design, I inspection. Stage: the review that closes the requirement (PDR, CDR, QR, AR) "
                   "or IOV, in-orbit verification. Stakeholder needs are in the MRD; x",
             "fr": "Priorité : 1 obligatoire (la mission ou une licence échoue sans elle), 2 nécessaire à la pleine "
                   "performance, 3 objectif. Méthodes de vérification (ECSS-E-ST-10-02C) : T essai (y compris "
                   "démonstration), A analyse, R revue de conception, I inspection. Étape : la revue qui clôt "
                   "l’exigence (PDR, CDR, QR, AR) ou IOV, vérification en orbite. Les besoins des parties prenantes "
                   "sont dans le MRD ; les exigences d’interface générées à partir des liaisons sont dans l’IRD."},
    "docs": {"en": "Applicable and reference documents", "fr": "Documents applicables et de référence"},
    "sysdesc": {"en": "System description", "fr": "Description du système"},
    "env": {"en": "Environment", "fr": "Environnement"},
    "orbit": {"en": "Operational orbit", "fr": "Orbite opérationnelle"},
    "launch": {"en": "Launch and deployment", "fr": "Lancement et déploiement"},
    "space_env": {"en": "Space environment requirements", "fr": "Exigences d’environnement spatial"},
    "reqs": {"en": "Requirements by type", "fr": "Exigences par type"},
    "summary": {"en": "Summary and open items", "fr": "Synthèse et points ouverts"},
    "verif": {"en": "Verification", "fr": "Vérification"},
    "verif_txt": {"en": "Every requirement is verified by at least one method; the verification plan (VP) gives the "
                        "model philosophy, the test campaign and the verification matrix, and the verification "
                        "control document (VCD) tracks the close-out.",
                  "fr": "Chaque exigence est vérifiée par au moins une méthode ; le plan de vérification (VP) donne la "
                        "philosophie des modèles, la campagne d’essais et la matrice de vérification, et le document "
                        "de contrôle de la vérification (VCD) suit la clôture."},
    "none": {"en": "No requirements have been entered for this study.",
             "fr": "Aucune exigence n’a été saisie pour cette étude."},
    "count": {"en": "{n} requirements in {g} groups (by level, then code, in each group).",
              "fr": "{n} exigences en {g} groupes (par niveau, puis par code, dans chaque groupe)."},
    "no_orbit": {"en": "The operational orbit is not defined yet (Mission tab).",
                 "fr": "L’orbite opérationnelle n’est pas encore définie (onglet Mission)."},
    "no_launch": {"en": "No launch segment element is recorded yet.",
                  "fr": "Aucun élément du segment lancement n’est encore enregistré."},
    "levels": {"en": "Test levels: {src}.", "fr": "Niveaux d’essai : {src}."},
    "no_env": {"en": "No environmental requirement is recorded yet.",
               "fr": "Aucune exigence d’environnement n’est encore enregistrée."},
    "open": {"en": "{n} requirements are flagged as open items (TBC/TBD):",
             "fr": "{n} exigences sont signalées comme points ouverts (à confirmer / à définir) :"},
}
_COLS = {
    "en": ["Code", "Requirement", "Threshold", "Unit", "Pri.", "Level", "Category", "Method", "Ver. level", "Stage",
           "Parents", "Allocated to", "Rationale"],
    "fr": ["Code", "Exigence", "Seuil", "Unité", "Prio.", "Niveau", "Catégorie", "Méthode", "Niv. vérif.", "Étape",
           "Mères", "Allouée à", "Justification"],
}
_WIDTHS = [2.2, 5.6, 1.6, 1.4, 0.8, 1.4, 1.6, 1.0, 1.4, 1.0, 2.2, 2.2, 3.8]


def _row(r: dict[str, Any]) -> list[Any]:
    parents = r.get("parent_codes") or ([r["parent_code"]] if r.get("parent_code") else [])
    return [r.get("code") or r.get("id", ""), r.get("text") or "", threshold_value_text(r),
            r.get("threshold_unit") or r.get("unit") or "", r.get("priority"), r.get("level") or "",
            r.get("category") or "", _methods(r), r.get("verification_level") or "",
            r.get("verification_phase") or "", parents, r.get("allocated_to") or "", r.get("rationale") or ""]


def build_ts(name: str, reqs: list[dict[str, Any]], *, need: dict | None = None, orbit: dict | None = None,
             launch: list[str] | None = None, env_levels: dict | None = None, lang: str = "en") -> bytes:
    lang = "fr" if str(lang or "").lower().startswith("fr") else "en"

    def T(key: str, **kw: Any) -> str:
        return _TXT[key][lang].format(**kw)

    doc = Document()
    _setup_styles(doc)
    _setup_margins(doc)
    _add_cover_page(doc, T("title"), "ECSS-E-ST-10-06C Annex A", name)
    _add_toc_placeholder(doc)
    _add_footer(doc, name, "TS")

    _add_section(doc, "1", T("intro"))
    _add_section(doc, "1.1", T("purpose_h"), T("purpose", name=name))
    _add_section(doc, "1.2", T("conv_h"), T("conv"))

    _add_section(doc, "2", T("docs"))
    for d in ("ECSS-E-ST-10-06C — Technical requirements specification",
              "ECSS-E-ST-10C — System engineering general requirements",
              "ECSS-E-ST-10-02C — Verification", "ECSS-E-ST-10-03C — Testing",
              "ECSS-E-ST-10-04C — Space environment", "CubeSat Design Specification rev. 14.1",
              "ISO 24113 — Space debris mitigation requirements"):
        doc.add_paragraph(d, style="List Bullet")

    _add_section(doc, "3", T("sysdesc"))
    need = need or {}
    doc.add_paragraph(need.get("problem_statement") or "—")
    if need.get("conops_summary"):
        doc.add_paragraph(need["conops_summary"])

    reqs = [r for r in reqs if r.get("level") != "stakeholder" and not r.get("generated_interface")
            and not str(r.get("code") or "").startswith("IR-")]
    groups: dict[str, list[dict]] = {g: [] for g in GROUPS}
    for r in reqs:
        groups[group_of(r)].append(r)
    for g in groups.values():
        g.sort(key=_level_key)

    # 4 environment: orbit, launch, space environment requirements
    _add_section(doc, "4", T("env"))
    _add_section(doc, "4.1", T("orbit"))
    orbit = orbit or {}
    if orbit.get("altitude_km"):
        rows = [[k, v] for k, v in (
            ("Orbit type" if lang == "en" else "Type d’orbite", str(orbit.get("orbit_type") or "").upper()),
            ("Altitude (km)", orbit.get("altitude_km")), ("Inclination (deg)" if lang == "en" else "Inclinaison (deg)",
                                                          orbit.get("inclination_deg")),
            ("Eccentricity" if lang == "en" else "Excentricité", orbit.get("eccentricity")),
            ("LTAN" if lang == "en" else "HLNA", orbit.get("ltan")),
            ("Period (min)" if lang == "en" else "Période (min)", orbit.get("period_min")),
            ("Longest eclipse (min)" if lang == "en" else "Éclipse la plus longue (min)", orbit.get("eclipse_duration_min")),
            ("Orbits per day" if lang == "en" else "Orbites par jour", orbit.get("orbits_per_day")),
            ("Mission duration (years)" if lang == "en" else "Durée de mission (années)", orbit.get("mission_duration_years")),
        ) if v not in (None, "", 0) or k.startswith(("Eccentricity", "Excentricité"))]
        _add_table(doc, ["Parameter" if lang == "en" else "Paramètre", "Value" if lang == "en" else "Valeur"],
                   [[k, _num(v)] for k, v in rows])
    else:
        doc.add_paragraph(T("no_orbit"))
    _add_section(doc, "4.2", T("launch"))
    if launch:
        for x in launch:
            doc.add_paragraph(x, style="List Bullet")
    else:
        doc.add_paragraph(T("no_launch"))
    env_levels = env_levels or {}
    if env_levels.get("level_source"):
        doc.add_paragraph(T("levels", src=env_levels["level_source"]))
        qs = env_levels.get("quasi_static") or {}
        rows = []
        if qs.get("axial_g") is not None:
            rows.append(["Quasi-static (axial / lateral, g)" if lang == "en" else "Quasi-statique (axial / latéral, g)",
                         f"{_num(qs.get('axial_g'))} / {_num(qs.get('lateral_g'))}"])
        for k, lab in (("sine", "Sine" if lang == "en" else "Sinus"), ("random", "Random" if lang == "en" else "Aléatoire"),
                       ("tvac", "Thermal vacuum" if lang == "en" else "Vide thermique")):
            v = env_levels.get(k) or {}
            if v:
                rows.append([lab, ", ".join(f"{kk} {_num(vv)}" for kk, vv in v.items()
                                            if kk != "note" and not isinstance(vv, (dict, list)))
                             + (f" ({v['note']})" if v.get("note") else "")])
        if rows:
            _add_table(doc, ["Environment" if lang == "en" else "Environnement", "Level" if lang == "en" else "Niveau"], rows)
    _add_section(doc, "4.3", T("space_env"))
    env_rows = groups["environmental"]
    if env_rows:
        _add_table(doc, ["Code", "Requirement" if lang == "en" else "Exigence", "Threshold" if lang == "en" else "Seuil",
                         "Source"],
                   [[r.get("code") or "", r.get("text") or "", threshold_text(r), r.get("source_ref") or ""] for r in env_rows])
    else:
        doc.add_paragraph(T("no_env"))

    # 5 requirements by type (landscape: thirteen columns)
    _orient(doc, landscape=True)
    _add_section(doc, "5", T("reqs"))
    present = [g for g in GROUPS if groups[g]]
    if reqs:
        doc.add_paragraph(T("count", n=len(reqs), g=len(present)))
        for i, g in enumerate(present, start=1):
            _add_section(doc, f"5.{i}", f"{GROUP_TITLES[g][lang]} ({len(groups[g])})")
            _compact_table(doc, _COLS[lang], [_row(r) for r in groups[g]], widths_cm=_WIDTHS, font_pt=7.5)
    else:
        doc.add_paragraph(T("none"))
    _orient(doc, landscape=False)

    # 6 summary
    _add_section(doc, "6", T("summary"))
    levels = [lv for lv in LEVEL_ORDER if any(r.get("level") == lv for r in reqs)]
    if reqs:
        _add_table(doc, ["Group" if lang == "en" else "Groupe"] + levels + ["Total"],
                   [[GROUP_TITLES[g][lang]] + [str(sum(1 for r in groups[g] if r.get("level") == lv)) for lv in levels]
                    + [str(len(groups[g]))] for g in present]
                   + [["Total"] + [str(sum(1 for r in reqs if r.get("level") == lv)) for lv in levels] + [str(len(reqs))]])
    open_items = [r for r in reqs if r.get("open_item")]
    if open_items:
        doc.add_paragraph(T("open", n=len(open_items)))
        _add_table(doc, ["Code", "Source"], [[r.get("code") or "", r.get("source_ref") or ""] for r in open_items])

    _add_section(doc, "7", T("verif"), T("verif_txt"))

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def _segment_of(eid: Any, els: dict[str, dict]) -> str:
    cur, n = els.get(eid) or {}, 0
    while cur and not cur.get("segment") and cur.get("parent_id") in els and n < 50:
        cur, n = els[cur["parent_id"]], n + 1
    return (cur or {}).get("segment") or ""


def launch_lines(elements: list[dict[str, Any]]) -> list[str]:
    """One line per launch segment element (launcher, deployer...), with its launch facts."""
    els = {e.get("id"): e for e in elements if e.get("id")}
    out = []
    for e in elements:
        if e.get("element_type") == "segment" or _segment_of(e.get("id"), els) != "launch":
            continue
        perf = e.get("performance") if isinstance(e.get("performance"), dict) else {}
        facts = [f"{k.replace('_', ' ')}: {_num(v)}" for k, v in perf.items()
                 if v not in (None, "", [], {}) and not isinstance(v, (dict, list))][:6]
        out.append(e.get("name", "") + (f" ({'; '.join(facts)})" if facts else "")
                   + (f" — {e['description']}" if e.get("description") else ""))
    return out


def requirement_rows(sx_requirements: list[dict], elements: list[dict]) -> list[dict]:
    """Collected requirements with ``allocated_to`` (element name) and ``parent_codes``."""
    names = {e.get("id"): e.get("name") for e in elements}
    codes = {r.get("id"): (r.get("code") or r.get("id")) for r in sx_requirements}
    out = []
    for r in sx_requirements:
        pids = r.get("parent_ids") or [p for p in [r.get("parent_id") or r.get("derived_from_requirement_id")] if p]
        out.append({**r, "parent_codes": [codes.get(p, p) for p in pids],
                    "allocated_to": names.get(r.get("element_id"), "") if r.get("element_id") else ""})
    return out


def generate_ts_from_export(sx: Any, lang: str = "en") -> bytes:
    """The TS of a collected study (``export_context.StudyExport``: need, mission, elements,
    requirements; ``ait`` for the test levels)."""
    elements = (getattr(sx, "elements", None) or {}).get("items") or []
    reqs = requirement_rows((getattr(sx, "requirements", None) or {}).get("items") or [], elements)
    mission = getattr(sx, "mission", None) or {}
    orbit = mission.get("orbit") or (mission.get("definition") or {}).get("orbit") or {}
    env = (getattr(sx, "ait", None) or {}).get("environment") or {}
    return build_ts(getattr(sx, "study_name", "") or "", reqs, need=getattr(sx, "need", None) or {}, orbit=orbit,
                    launch=launch_lines(elements), env_levels=env, lang=lang)


def generate_ts_docx(study_name: str, data: dict[str, Any]) -> bytes:
    """Legacy entry (``/docx/ts`` without a study): the ``data`` dict of the docx route."""
    reqs = [{**r, "parent_codes": r.get("parent_codes") or ([r["parent_code"]] if r.get("parent_code") else [])}
            for r in data.get("requirements") or []]
    return build_ts(study_name, reqs, need=data.get("mission_need") or {}, orbit=data.get("orbit") or {},
                    launch=launch_lines(data.get("elements") or []))
