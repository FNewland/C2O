#!/usr/bin/env python3
"""Generate the ORBIT NORTH outcomes map (instructor document, EN + FR) from
configs/outcomes/orbit_north_outcomes.yaml, and check every ID it names.

    python3 tools/gen_outcomes.py            # write docs/orbit_north/OUTCOMES_MAP_{en,fr}.md
    python3 tools/gen_outcomes.py --check    # verify only (exit 1 on a problem)

Checks: every worksheet, decision group, video and question exists; every CLO and
course outcome referenced is defined; every worksheet, decision and video in the
course is tagged (nothing silently untagged).
"""
from __future__ import annotations

import argparse
import sys
from collections import OrderedDict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.i18n.typo import fix as fr_typo  # noqa: E402  (French spacing: NBSP / NNBSP)

DESIGN = Path(__file__).resolve().parents[1]
REPO = DESIGN.parent
SRC = DESIGN / "configs/outcomes/orbit_north_outcomes.yaml"
OUT = {"en": DESIGN / "docs/orbit_north/OUTCOMES_MAP_en.md",
       "fr": DESIGN / "docs/orbit_north/OUTCOMES_MAP_fr.md"}

T = {
    "title": {"en": "ORBIT NORTH — outcomes map (instructor)", "fr": "ORBIT NORTH — carte des résultats (enseignant)"},
    "intro": {
        "en": ("How ORBIT NORTH (GNG 3100 / SYS 5186) ties to the Master of Systems Engineering program "
               "outcomes (PLO framework, draft 7 November 2026), and how every assessment, worksheet, decision "
               "record, video and embedded question ties to both. **Instructor document**: students see the "
               "course outcomes and, for the large assessments, the rubrics and target level (syllabus); the "
               "tags for worksheets, decision records, videos and questions stay here.\n\n"
               "Generated from `configs/outcomes/orbit_north_outcomes.yaml` by `tools/gen_outcomes.py`; edit "
               "the YAML, not this file."),
        "fr": ("Comment ORBIT NORTH (GNG 3100 / SYS 5186) se rattache aux résultats du programme de maîtrise "
               "en ingénierie des systèmes (cadre des PLO, ébauche du 7 novembre 2026), et comment chaque "
               "évaluation, fiche d’exercices, fiche de décision, vidéo et question intégrée se rattache aux "
               "deux. **Document de l’enseignant** : les étudiantes et étudiants voient les résultats du cours "
               "et, pour les grandes évaluations, les grilles et le niveau visé (plan de cours) ; les étiquettes "
               "des fiches, des décisions, des vidéos et des questions restent ici.\n\n"
               "Généré à partir de `configs/outcomes/orbit_north_outcomes.yaml` par `tools/gen_outcomes.py` ; "
               "modifier le YAML, pas ce fichier.")},
    "h_lo": {"en": "1. Course outcomes → program CLOs → PLOs", "fr": "1. Résultats du cours → CLO → PLO du programme"},
    "h_as": {"en": "2. Assessments", "fr": "2. Évaluations"},
    "h_label": {"en": "3. SYS 5186 Learning Facts label — proposal", "fr": "3. Étiquette Learning Facts de SYS 5186 — proposition"},
    "h_ws": {"en": "4. Worksheets (instructor only)", "fr": "4. Fiches d’exercices (enseignant seulement)"},
    "h_dec": {"en": "5. Decision records (instructor only)", "fr": "5. Fiches de décision (enseignant seulement)"},
    "h_vid": {"en": "6. Videos and embedded questions (instructor only)", "fr": "6. Vidéos et questions intégrées (enseignant seulement)"},
    "h_cov": {"en": "7. Coverage check", "fr": "7. Vérification de couverture"},
    "lo": {"en": "Course outcome", "fr": "Résultat du cours"},
    "clo": {"en": "Program CLOs", "fr": "CLO du programme"},
    "plo": {"en": "PLOs", "fr": "PLO"},
    "grad": {"en": " *(SYS 5186 only)*", "fr": " *(SYS 5186 seulement)*"},
    "new": {"en": "† not on the 7 Nov SYS 5186 label: proposed addition",
            "fr": "† absent de l’étiquette SYS 5186 du 7 nov. : ajout proposé"},
    "as": {"en": "Assessment", "fr": "Évaluation"},
    "w": {"en": "Weight UG / G", "fr": "Poids 1er c. / c. sup."},
    "rub": {"en": "Rubrics (CLO → PLO)", "fr": "Grilles (CLO → PLO)"},
    "seen": {"en": "Students see rubric", "fr": "Grille montrée"},
    "yes": {"en": "yes", "fr": "oui"}, "no": {"en": "no (tags only)", "fr": "non (étiquettes seulement)"},
    "targets": {"en": "Targets for the large assessments", "fr": "Cibles des grandes évaluations"},
    "lab_intro": {
        "en": ("The 7 Nov label shows SYS 5186 as introduce/develop only. The graded large assessments above "
               "produce assessed evidence, so the proposal adds **A** where a rubric is used and fills in the "
               "% of the course grade. **Estimate**: each assessment's SYS 5186 weight is split equally across "
               "the PLOs its rubrics roll up to; recompute once the marking rubrics are final."),
        "fr": ("L’étiquette du 7 nov. présente SYS 5186 comme introduction/développement seulement. Les grandes "
               "évaluations notées ci-dessus produisent des preuves évaluées : la proposition ajoute donc **A** là "
               "où une grille est utilisée et calcule le % de la note du cours. **Estimation** : le poids SYS 5186 "
               "de chaque évaluation est réparti également entre les PLO auxquels ses grilles se rattachent ; à "
               "recalculer quand les grilles de correction seront définitives.")},
    "row": {"en": "Row", "fr": "Ligne"}, "now": {"en": "7 Nov label", "fr": "Étiquette du 7 nov."},
    "prop": {"en": "Proposed", "fr": "Proposé"}, "pct": {"en": "% grade (est.)", "fr": "% de la note (est.)"},
    "clos_prop": {"en": "CLO tags, proposed", "fr": "Étiquettes CLO proposées"},
    "id": {"en": "ID", "fr": "ID"}, "name": {"en": "Title", "fr": "Titre"},
    "los": {"en": "Course outcomes", "fr": "Résultats du cours"},
    "vid": {"en": "Video", "fr": "Vidéo"}, "q": {"en": "Questions (type → CLOs)", "fr": "Questions (type → CLO)"},
    "group": {"en": "Records", "fr": "Fiches"},
    "cov_lo": {"en": "Where each course outcome is practised and assessed",
               "fr": "Où chaque résultat du cours est pratiqué et évalué"},
    "practised": {"en": "Practised in (worksheets · videos)", "fr": "Pratiqué dans (fiches · vidéos)"},
    "assessed": {"en": "Assessed in", "fr": "Évalué dans"},
}


def tr(d, lang):
    return d[lang] if isinstance(d, dict) else d


def load_ids():
    lw = yaml.safe_load((DESIGN / "configs/worksheets/learner_workbook.yaml").read_text())["worksheets"]
    ws = {w["id"]: tr(w["title"], "en") for w in lw}
    wfr = {w["id"]: (w["title"].get("fr") if isinstance(w["title"], dict) else w["title"]) for w in lw}
    ops = yaml.safe_load((REPO / "sim/configs/eosat1/worksheets/ops_week3.yaml").read_text())["worksheets"]
    for w in ops:
        if w["id"] in ("WB-5.4-Q", "WB-5.7-CE"):
            continue      # graded quiz (= assessment A5) and anonymous course evaluation: not tagged
        ws[w["id"]] = tr(w["title"], "en")
        wfr[w["id"]] = w["title"].get("fr") if isinstance(w["title"], dict) else w["title"]
    dec = yaml.safe_load((DESIGN / "configs/worksheets/decision_catalogue.yaml").read_text())
    dl = dec["decisions"]
    decs = [d["id"] for d in dl] if isinstance(dl, list) else list(dl)
    vids = {}
    for p in sorted((REPO / "video/storyboards").glob("*.yaml")):
        sb = yaml.safe_load(p.read_text())
        qs = [(st["id"], st["question"]["type"]) for st in sb.get("steps", []) if st.get("question")]
        vids[sb["id"]] = (sb["title"], qs)
    return ws, wfr, decs, vids


def lo_name(k):
    """LO1 -> 'LO 1', LOG2 -> 'LO G2'."""
    return "LO G" + k[3:] if k.startswith("LOG") else "LO " + k[2:]


def dec_group(did):
    return "-".join(did.split("-")[:2])         # D-2.4-MASS -> D-2.4, D-GATE-MDR -> D-GATE


def check(m, ws, decs, vids):
    errs = []
    clos, los = m["clos"], m["course_outcomes"]
    def chk_tags(where, t):
        for lo in t.get("los", []):
            if lo not in los:
                errs.append(f"{where}: unknown course outcome {lo}")
        for c in t.get("clos", []) + t.get("rubrics", []):
            if c not in clos:
                errs.append(f"{where}: unknown CLO {c}")
    for k, v in los.items():
        chk_tags(k, v)
    for k, v in m["assessments"].items():
        chk_tags(k, v)
    for k, v in m["worksheets"].items():
        if k not in ws:
            errs.append(f"worksheet {k} does not exist")
        chk_tags(k, v)
    for k in ws:
        if k not in m["worksheets"]:
            errs.append(f"worksheet {k} is not tagged")
    groups = m["decision_groups"]
    for d in decs:
        if dec_group(d) not in groups:
            errs.append(f"decision {d}: group {dec_group(d)} is not tagged")
    for k, v in groups.items():
        chk_tags(k, v)
    for k, v in m["videos"].items():
        if k not in vids:
            errs.append(f"video {k} does not exist")
        chk_tags(k, v)
    for k in vids:
        if k not in m["videos"]:
            errs.append(f"video {k} is not tagged")
    return errs


def label_proposal(m):
    clos = m["clos"]
    shares: dict[str, float] = OrderedDict((p, 0.0) for p in m["plos"])
    assessed = set()
    for a in m["assessments"].values():
        plos = list(OrderedDict.fromkeys(clos[c]["plo"] for c in a["rubrics"]))
        for p in plos:
            shares[p] += a["weight"]["SYS5186"] / len(plos)
            assessed.add(p)
    developed = set()
    for group in ("worksheets", "decision_groups", "videos"):
        for t in m[group].values():
            developed |= {clos[c]["plo"] for c in t.get("clos", [])}
    return shares, assessed, developed


LABEL_NOW = {"PLO1": "I D", "PLO2": "I", "PLO3": "I", "PLO4": "I", "PLO5": "I D",
             "PLO6-MEng": "I", "PLO6-MASc": "—", "GDLE6": "—"}


def render(m, lang, ws, wfr, decs, vids):
    L = lambda k: T[k][lang]  # noqa: E731
    clos, los, plos = m["clos"], m["course_outcomes"], m["plos"]
    cl = lambda c: f"{c}{'' if clos[c]['on_label'] else '†'}"  # noqa: E731
    clo_txt = lambda cs: ", ".join(f"{cl(c)} {clos[c][lang]}" for c in cs)  # noqa: E731
    plo_of = lambda cs: ", ".join(OrderedDict.fromkeys(clos[c]["plo"] for c in cs))  # noqa: E731
    o = [f"# {L('title')}", "", f"*{m['version']}*", "", L("intro"), ""]

    o += [f"## {L('h_lo')}", "", f"| {L('lo')} | {L('clo')} | {L('plo')} |", "|---|---|---|"]
    for k, v in los.items():
        o.append(f"| **{lo_name(k)}** {v[lang]}{L('grad') if v.get('grad') else ''} | {clo_txt(v['clos'])} | {plo_of(v['clos'])} |")
    o += ["", L("new"), "", "| PLO | " + ("Nom" if lang == "fr" else "Name") + " | GDLE |", "|---|---|---|"]
    for k, v in plos.items():
        o.append(f"| {k} | {v[lang]} | {', '.join(map(str, v['gdle']))} |")

    o += ["", f"## {L('h_as')}", "",
          f"| {L('as')} | {L('w')} | {L('los')} | {L('rub')} | {L('seen')} |", "|---|---|---|---|---|"]
    for k, a in m["assessments"].items():
        lo = ", ".join(lo_name(x) for x in a["los"])
        rub = "; ".join(f"{cl(c)} {clos[c][lang]} → {clos[c]['plo']}" for c in a["rubrics"])
        o.append(f"| {k} {a[lang]} | {a['weight']['GNG3100']} % / {a['weight']['SYS5186']} % | {lo} | {rub} | "
                 f"{L('yes') if a['large'] else L('no')} |")
    o += ["", f"**{L('targets')}**", "", f"- GNG 3100: {m['targets']['GNG3100'][lang]}",
          f"- SYS 5186: {m['targets']['SYS5186'][lang]}"]

    shares, assessed, developed = label_proposal(m)
    o += ["", f"## {L('h_label')}", "", L("lab_intro"), "",
          f"| {L('row')} | {L('now')} | {L('prop')} | {L('pct')} |", "|---|---|---|---:|"]
    for p, v in plos.items():
        idas = ["I"] + (["D"] if p in developed else []) + (["A"] if p in assessed else [])
        if p == "PLO6-MASc" and p not in assessed and p not in developed:
            idas = ["—"]
        pct = f"{shares[p]:.1f} %" if shares[p] else "—"
        o.append(f"| {p} {v[lang]} | {LABEL_NOW.get(p, '—')} | {' '.join(idas)} | {pct} |")
    used = sorted({c for t in list(m["assessments"].values()) + list(m["course_outcomes"].values())
                   for c in t.get("rubrics", []) + t.get("clos", [])}, key=lambda s: [float(x) for x in s.split(".")])
    o += ["", f"{L('clos_prop')}: " + ", ".join(cl(c) for c in used) + ".", "", L("new")]

    o += ["", f"## {L('h_ws')}", "", f"| {L('id')} | {L('name')} | {L('los')} | {L('clo')} |", "|---|---|---|---|"]
    names = wfr if lang == "fr" else ws
    for k, v in m["worksheets"].items():
        o.append(f"| {k} | {names.get(k) or ws.get(k, '')} | {', '.join(map(lo_name, v['los']))} | {clo_txt(v['clos'])} |")

    o += ["", f"## {L('h_dec')}", "", f"| {L('group')} | {L('los')} | {L('clo')} |", "|---|---|---|"]
    for g, v in m["decision_groups"].items():
        members = [d for d in decs if dec_group(d) == g]
        o.append(f"| {g}-* ({len(members)}) | {', '.join(map(lo_name, v['los']))} | {clo_txt(v['clos'])} |")

    o += ["", f"## {L('h_vid')}", "", f"| {L('vid')} | {L('los')} | {L('clo')} | {L('q')} |", "|---|---|---|---|"]
    add = m.get("reflect_adds_clo")
    for k, v in m["videos"].items():
        title, qs = vids[k]
        q = "; ".join(f"{sid} ({typ}) → {', '.join(cl(c) for c in v['clos'] + ([add] if typ == 'reflect' and add not in v['clos'] else []))}"
                      for sid, typ in qs)
        o.append(f"| {k} {tr(title, lang)} | {', '.join(map(lo_name, v['los']))} | {clo_txt(v['clos'])} | {q} |")

    o += ["", f"## {L('h_cov')}", "", f"**{L('cov_lo')}**", "",
          f"| {L('lo')} | {L('practised')} | {L('assessed')} |", "|---|---|---|"]
    for k in los:
        wsx = [w for w, v in m["worksheets"].items() if k in v["los"]]
        vx = [w for w, v in m["videos"].items() if k in v["los"]]
        ax = [a for a, v in m["assessments"].items() if k in v["los"]]
        o.append(f"| {lo_name(k)} | {len(wsx)} · {len(vx)} | {', '.join(ax) or '**—**'} |")
    return "\n".join(o) + "\n"

SYLLABUS = {"en": DESIGN / "docs/orbit_north/syllabus_en.md", "fr": DESIGN / "docs/orbit_north/syllabus_fr.md"}

S = {
    "plo_h": {"en": "### How these outcomes connect to the Master of Systems Engineering",
              "fr": "### Lien entre ces résultats et la maîtrise en ingénierie des systèmes"},
    "plo_p": {"en": ("For SYS 5186 students, ORBIT NORTH counts towards the program learning outcomes (PLOs) of "
                     "the Master of Systems Engineering; GNG 3100 work is marked with the same rubrics. Each course outcome below builds one or more of the program's course-level "
                     "outcomes (CLOs), and each CLO belongs to a PLO. The same five-level rubric scale is used "
                     "throughout the program: 1 Initial thoughts, 2 First engagement, 3 Deeper engagement, "
                     "4 First leadership, 5 Deeper leadership."),
              "fr": ("Pour les étudiantes et étudiants de SYS 5186, ORBIT NORTH contribue aux résultats "
                     "d’apprentissage du programme (PLO) de la maîtrise en ingénierie des systèmes ; les travaux de "
                     "GNG 3100 sont corrigés avec les mêmes grilles. Chaque résultat du cours ci-dessous développe un ou plusieurs "
                     "résultats de cours du programme (CLO), et chaque CLO relève d’un PLO. La même échelle de "
                     "grilles à cinq niveaux sert dans tout le programme : 1 Premières réflexions, 2 Premier "
                     "engagement, 3 Engagement approfondi, 4 Premier leadership, 5 Leadership approfondi.")},
    "as_h": {"en": "### What the major assessments assess", "fr": "### Ce qu’évaluent les grandes évaluations"},
    "as_p": {"en": ("The major assessments are marked with the program rubrics listed below (posted in "
                    "Brightspace). The quizzes and the daily CDF worksheets are marked on their own keys."),
             "fr": ("Les grandes évaluations sont corrigées avec les grilles du programme indiquées ci-dessous "
                    "(publiées dans Brightspace). Les quiz et les cahiers d’exercices quotidiens du CDF sont "
                    "corrigés selon leur propre corrigé.")},
    "level_h": {"en": "Level expected", "fr": "Niveau attendu"},
    "rubric": {"en": "Program rubrics (CLO → PLO)", "fr": "Grilles du programme (CLO → PLO)"},
}


def render_syllabus(m, lang):
    clos, los = m["clos"], m["course_outcomes"]
    L = lambda k: T[k][lang]  # noqa: E731
    plo_name = lambda p: m["plos"][p][lang]  # noqa: E731
    a = [S["plo_h"][lang], "", S["plo_p"][lang], "",
         f"| {L('lo')} | {L('clo')} | {L('plo')} |", "|---|---|---|"]
    for k, v in los.items():
        cs = ", ".join(f"{c} {clos[c][lang]}" for c in v["clos"])
        ps = ", ".join(f"{p} {plo_name(p)}" for p in OrderedDict.fromkeys(clos[c]["plo"] for c in v["clos"]))
        a.append(f"| {lo_name(k)} | {cs} | {ps} |")
    b = [S["as_h"][lang], "", S["as_p"][lang], "",
         f"| {L('as')} | {L('los')} | {S['rubric'][lang]} |", "|---|---|---|"]
    for k, x in m["assessments"].items():
        if not x["large"]:
            continue
        rub = "; ".join(f"{c} {clos[c][lang]} → {clos[c]['plo']}" for c in x["rubrics"])
        b.append(f"| {x[lang]} | {', '.join(map(lo_name, x['los']))} | {rub} |")
    b += ["", f"**{S['level_h'][lang]}**", "", f"- GNG 3100 : {m['targets']['GNG3100'][lang]}" if lang == "fr"
          else f"- GNG 3100: {m['targets']['GNG3100'][lang]}",
          f"- SYS 5186 : {m['targets']['SYS5186'][lang]}" if lang == "fr"
          else f"- SYS 5186: {m['targets']['SYS5186'][lang]}"]
    return "\n".join(a), "\n".join(b)


def fill(text, name, body):
    b, e = f"<!-- {name}:begin -->", f"<!-- {name}:end -->"
    i, j = text.index(b) + len(b), text.index(e)
    return text[:i] + "\n" + body + "\n" + text[j:]



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    m = yaml.safe_load(SRC.read_text())
    ws, wfr, decs, vids = load_ids()
    errs = check(m, ws, decs, vids)
    for e in errs:
        print("ERROR", e)
    if errs:
        return 1
    if a.check:
        print("outcomes map: ok")
        return 0
    for lang, path in OUT.items():
        doc = render(m, lang, ws, wfr, decs, vids)
        path.write_text(fr_typo(doc) if lang == "fr" else doc)
        print("wrote", path.relative_to(REPO))
        plo, assess = render_syllabus(m, lang)
        if lang == "fr":
            plo, assess = fr_typo(plo), fr_typo(assess)
        sy = SYLLABUS[lang].read_text()
        sy = fill(fill(sy, "outcomes-plo", plo), "outcomes-assess", assess)
        SYLLABUS[lang].write_text(sy)
        print("updated", SYLLABUS[lang].relative_to(REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
