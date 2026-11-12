"""Course manifest for the ORBIT NORTH open Moodle course (bilingual, ungraded).

Writes manifest.json for build_course.php. Every visible string is a
multilang pair: <span lang="en" class="multilang">…</span><span lang="fr" …>…</span>.
No assignment, quiz or other submission activity is created: the site is
outside the university firewall and holds no graded student work.
"""
from __future__ import annotations

import html
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "sim"))
sys.path.insert(0, str(REPO / "video"))
from tools.i18n.typo import fix as fr_fix  # noqa: E402
from c2ovideo import storyboard  # noqa: E402
from c2ovideo.storyboard import tr  # noqa: E402

VIDEOS = REPO / "video/out"
DECKS = REPO / "design/moodle/decks/out"
DECK_SRC = REPO / "design/moodle/decks/src"
PDF = Path(os.environ.get("C2O_PDF_DIR", REPO / "design/docs/pdf"))   # rebuild with docs/build_course_books.py first


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def fr(s: str) -> str:
    return fr_fix(s, markdown=False)


def ml(en: str, fr_: str, block: bool = False) -> str:
    """Multilang pair from plain text (escaped; French typography applied)."""
    tag = "div" if block else "span"
    return (f'<{tag} lang="en" class="multilang">{esc(en)}</{tag}>'
            f'<{tag} lang="fr" class="multilang">{esc(fr(fr_))}</{tag}>')


def _blocks(h: str) -> list[tuple[str, str, str]]:
    """Top-level (tag, attrs, inner) blocks of simple, flat HTML."""
    import re
    out = [(m.group(1), m.group(2), m.group(3)) for m in
           re.finditer(r"<(p|ul|div)([^>]*)>(.*?)</\1>", h, re.S)]
    assert "".join(f"<{t}{a}>{i}</{t}>" for t, a, i in out) == re.sub(r">\s+<", "><", h.strip()), h[:80]
    return out


def mlh(en_html: str, fr_html: str) -> str:
    """Multilang pair from ready HTML with the same block structure in both languages.

    The multilang filter needs <span lang> wrappers, and the HTML cleaner breaks a span
    that wraps a list, so the spans go inside each paragraph and list item.
    """
    import re
    sp = lambda a, b: (f'<span lang="en" class="multilang">{a}</span>'
                       f'<span lang="fr" class="multilang">{b}</span>')
    en_html = re.sub(r">\s+<", "><", en_html.strip()); fr_html = re.sub(r">\s+<", "><", fr_html.strip())
    eb, fb = _blocks(en_html), _blocks(fr_html)
    assert [t for t, _, _ in eb] == [t for t, _, _ in fb], (eb, fb)
    out = []
    for (t, a, ie), (_, af, if_) in zip(eb, fb):
        if t == "ul":
            le = re.findall(r"<li>(.*?)</li>", ie, re.S); lf = re.findall(r"<li>(.*?)</li>", if_, re.S)
            assert len(le) == len(lf)
            out.append("<ul>" + "".join(f"<li>{sp(x, y)}</li>" for x, y in zip(le, lf)) + "</ul>")
        elif t == "div":      # an H5P placeholder: one whole div per language
            out.append(sp(f"<div{a}>{ie}</div>", f"<div{af}>{if_}</div>"))
        else:
            out.append(f"<p{a}>{sp(ie, if_)}</p>" if a == af else sp(f"<p{a}>{ie}</p>", f"<p{af}>{if_}</p>"))
    return "".join(out)


LANG_CSS = ("<style>body:not(.lang-fr) .c2o-fr, body.lang-fr .c2o-en{display:none}"
            ".c2o-en table, .c2o-fr table{font-size:.85rem}</style>")


def mlr(en_html: str, fr_html: str) -> str:
    """Multilang pair for rich HTML (headings, ordered lists, tables), which the multilang filter's
    <span> wrappers cannot hold: two blocks, the one for the other language hidden by Moodle's
    body class (lang-en / lang-fr)."""
    return f'{LANG_CSS}<div class="c2o-en" lang="en">{en_html}</div><div class="c2o-fr" lang="fr">{fr_html}</div>'


def p(t: str) -> str:
    return f"<p>{t}</p>"


SB = {sb.id: sb for sb in storyboard.all_storyboards()}

PRACTICE = ("Questions in the video are for practice. Your answers are kept on this site only to unlock the next "
            "item and for anonymous course statistics; they are never graded. Watch to the end and press Submit to "
            "finish the video.",
            "Les questions de la vidéo servent à s'exercer. Vos réponses ne sont conservées sur ce site que pour "
            "débloquer l'élément suivant et pour des statistiques anonymes du cours ; elles ne sont jamais notées. "
            "Regardez jusqu'à la fin et appuyez sur Soumettre pour terminer la vidéo.")
LANG_NAME = {"en": ("English", "anglais"), "fr": ("French", "français")}


def video_items(vid: str) -> list[dict]:
    """One tracked H5P activity per language (mod_h5pactivity): attempts and answers are recorded,
    which is what unlocks the next item and feeds the instructor dashboard (aggregates only)."""
    sb = SB[vid]
    slug = sb.slug
    out = []
    for lang in ("en", "fr"):
        pkg = VIDEOS / slug / f"{slug}.{lang}.h5p"
        if not pkg.exists() and os.environ.get("C2O_MANIFEST_DRY"):
            pass
        else:
            assert pkg.exists(), pkg
        summ_en = tr(sb.raw.get("summary") or {}, "en") or ""
        summ_fr = fr(tr(sb.raw.get("summary") or {}, "fr") or "")
        intro = mlh(p(esc(summ_en)) + f'<p class="small text-muted">{esc(PRACTICE[0])}</p>',
                    p(esc(summ_fr)) + f'<p class="small text-muted">{esc(fr(PRACTICE[1]))}</p>')
        ln_en, ln_fr = LANG_NAME[lang]
        name = ml(f"Video · {tr(sb.title, 'en')} · {ln_en}", f"Vidéo · {tr(sb.title, 'fr')} · {ln_fr}")
        out.append({"type": "h5pactivity", "name": name, "intro": intro, "lang": lang, "video": vid,
                    # a video with questions is complete when its answers are recorded; a walkthrough
                    # without questions sends no score, so opening it is what counts
                    "graded": any(st.question for st in sb.steps),
                    "file": {"name": pkg.name, "path": str(pkg)}, "idnumber": f"{vid}-{lang.upper()}"})
    return out


def deck_title(did: str) -> tuple[str, str]:
    import yaml
    d = yaml.safe_load((DECK_SRC / f"{did}.yaml").read_text())
    return d["title"]["en"], d["title"]["fr"]


def pdf_viewer(fname: str, label: str) -> str:
    return (f'<p><a href="@@PLUGINFILE@@/{fname}">{esc(label)}</a></p>'
            f'<p><iframe src="@@PLUGINFILE@@/{fname}" title="{esc(label)}" '
            f'style="width:100%;height:640px;border:1px solid #ccc"></iframe></p>')


def deck_item(did: str) -> dict:
    en, fr_ = deck_title(did)
    files = []
    for lang in ("en", "fr"):
        f = DECKS / f"{did}.{lang}.pdf"
        assert f.exists(), f
        files.append({"name": f"ORBIT_NORTH_{did}_{lang.upper()}.pdf", "path": str(f)})
    content = mlh(pdf_viewer(files[0]["name"], "Download the slides (PDF)"),
                  pdf_viewer(files[1]["name"], fr("Télécharger les diapositives (PDF)")))
    return {"type": "page", "name": ml("Slides · " + en, "Diapositives · " + fr_), "content": content,
            "files": files, "idnumber": f"DECK-{did}"}


def doc_list_item(name_en, name_fr, intro_en, intro_fr, docs, idnumber) -> dict:
    """A page listing PDFs, one list per language. docs: [(label_en, label_fr, en_path, fr_path)]."""
    files, li = [], {"en": [], "fr": []}
    for le, lf, pe, pf in docs:
        for lang, path, label in (("en", pe, le), ("fr", pf, lf)):
            path = Path(path)
            assert path.exists(), path
            files.append({"name": path.name, "path": str(path)})
            b = path.stat().st_size
            size = (f"{b / 1e6:.1f} " + ("MB" if lang == "en" else "Mo")) if b >= 1e6 else \
                   (f"{b / 1e3:.0f} " + ("KB" if lang == "en" else "ko"))
            lab = label if lang == "en" else fr(label)
            li[lang].append(f'<li><a href="@@PLUGINFILE@@/{path.name}">{esc(lab)}</a> '
                            f'&nbsp;<span class="text-muted">(PDF, {size})</span></li>')
    content = mlh(p(esc(intro_en)) + "<ul>" + "".join(li["en"]) + "</ul>",
                  p(esc(fr(intro_fr))) + "<ul>" + "".join(li["fr"]) + "</ul>")
    return {"type": "page", "name": ml(name_en, name_fr), "content": content, "files": files,
            "idnumber": idnumber}


class Summary:
    """A section summary kept as its parts, so the 12-week layout can give the same
    section its own agenda lines (lecture and studio instead of morning and afternoon)."""

    def __init__(self, theme_en, theme_fr, lines, reading):
        self.theme_en, self.theme_fr, self.lines, self.reading = theme_en, theme_fr, lines, reading

    def render(self, lines=None) -> str:
        return _summary_html(self.theme_en, self.theme_fr, lines or self.lines, self.reading)


def summary(theme_en, theme_fr, lines, reading) -> Summary:
    return Summary(theme_en, theme_fr, lines, reading)


def _summary_html(theme_en, theme_fr, lines, reading):
    """Section summary: theme, agenda lines [(en, fr)], OER reading (en, fr)."""
    def block(lang):
        t = theme_en if lang == "en" else fr(theme_fr)
        items = "".join(f"<li>{esc(a if lang == 'en' else fr(b))}</li>" for a, b in lines)
        r = reading[0] if lang == "en" else fr(reading[1])
        lab = "Reading" if lang == "en" else "Lecture"
        return (f"<p><strong>{esc(t)}</strong></p><ul>{items}</ul>"
                f"<p><em>{lab}</em>{' : ' if lang == 'fr' else ': '}{esc(r)}</p>").replace(" : ", " : ")
    return mlh(block("en"), block("fr"))


OER = ("Concurrent Spacecraft Design (open textbook), ", "Concurrent Spacecraft Design (manuel libre), ")


def oer(ch_en: str, ch_fr: str) -> tuple[str, str]:
    return OER[0] + ch_en, OER[1] + ch_fr


W3 = PDF / "en", PDF / "fr"


def w3(stem: str) -> tuple[str, str]:
    return str(W3[0] / f"ORBIT_NORTH_W3_{stem}.pdf"), str(W3[1] / f"ORBIT_NORTH_W3_{stem}_FR.pdf")


SECTIONS = [
    {
        "name": ml("Week 1 · Day 1 — Canada in space, onboarding and the concurrent design method",
                   "Semaine 1 · Jour 1 — Le Canada dans l'espace, accueil et méthode de conception concurrente"),
        "summary": summary(
            "Canada's space sector past, present and emerging; teams and roles; a first look at regulation; the SpaceCDF platform.",
            "Le secteur spatial canadien d'hier, d'aujourd'hui et de demain ; équipes et rôles ; premier regard sur la réglementation ; la plateforme SpaceCDF.",
            [("Morning: Canadian space ecosystem and course onboarding; team formation and role assignment",
              "Matin : écosystème spatial canadien et accueil du cours ; formation des équipes et attribution des rôles"),
             ("Afternoon: regulatory teaser; concurrent design method; teams open a mission file",
              "Après-midi : survol réglementaire ; méthode de conception concurrente ; les équipes ouvrent un dossier de mission")],
            oer("chapters 1 and 2 (2.1–2.4)", "chapitres 1 et 2 (2.1 à 2.4)")),
        "items": ["DECK:L01", "DECK:L02", "V-DES-01", "V-DES-02", "V-SCDF-01", "V-SCDF-14"],
    },
    {
        "name": ml("Week 1 · Day 2 — Mission architecture, concept and the informal MCR",
                   "Semaine 1 · Jour 2 — Architecture de mission, concept et MCR informelle"),
        "summary": summary(
            "From a mission need to concept v0 and a first concept of operations, presented at an informal Mission Concept Review.",
            "D'un besoin de mission au concept v0 et à un premier concept d'opérations, présentés à une revue de concept de mission informelle.",
            [("Morning: mission alternatives trade; ConOps v0; first parametric budgets",
              "Matin : étude des options de mission ; ConOps v0 ; premiers bilans paramétriques"),
             ("Afternoon: concept refinement; risk register opened; informal MCR",
              "Après-midi : affinage du concept ; ouverture du registre des risques ; MCR informelle")],
            oer("chapter 4", "chapitre 4")),
        "items": ["DECK:L03", "V-DES-03", "V-SCDF-08", "V-SCDF-17", "V-SCDF-06", "V-SCDF-07"],
    },
    {
        "name": ml("Week 2 · Day 1 — Concept lock and the Canadian regulatory landscape",
                   "Semaine 2 · Jour 1 — Concept figé et paysage réglementaire canadien"),
        "summary": summary(
            "Close the MCR actions, lock concept v1, write top-level requirements; then the rules every Canadian mission meets.",
            "Clore les actions de la MCR, figer le concept v1, rédiger les exigences de haut niveau ; puis les règles que rencontre toute mission canadienne.",
            [("Morning: MCR action closure; concept v1; programmatic envelope; risk register v0",
              "Matin : clôture des actions de la MCR ; concept v1 ; enveloppe programmatique ; registre des risques v0"),
             ("Afternoon: remote sensing licences, spectrum, export control, debris; the two-page regulatory brief",
              "Après-midi : licences de télédétection, spectre, contrôle des exportations, débris ; la note réglementaire de deux pages")],
            oer("chapter 2 (2.5 onward) and chapter 3", "chapitre 2 (à partir de 2.5) et chapitre 3")),
        "items": ["DECK:L04", "V-SCDF-11", "DECK:L05", "V-SCDF-21"],
    },
    {
        "name": ml("Week 2 · Day 2 — CDF Day 1: System-V, requirements and first budgets",
                   "Semaine 2 · Jour 2 — Jour 1 de CDF : cycle en V, exigences et premiers bilans"),
        "summary": summary(
            "Requirements that say what, not how; a function tree; mass, power, data and link budgets with margins.",
            "Des exigences qui disent quoi, et non comment ; un arbre fonctionnel ; bilans de masse, d'énergie, de données et de liaison avec marges.",
            [("System-V briefing; tailoring; lifecycle gate map", "Présentation du cycle en V ; adaptation ; carte des jalons du cycle de vie"),
             ("SMART requirements; functional decomposition; first parametric budgets",
              "Exigences SMART ; décomposition fonctionnelle ; premiers bilans paramétriques")],
            oer("chapters 5, 6 and 8", "chapitres 5, 6 et 8")),
        "items": ["DECK:L06", "V-DES-04", "V-SCDF-04", "V-SCDF-12", "V-DES-06", "V-SCDF-02", "V-SCDF-18",
                  "V-SCDF-22"],
    },
    {
        "name": ml("Week 2 · Day 3 — CDF Day 2: orbit, power, AOCS and thermal",
                   "Semaine 2 · Jour 3 — Jour 2 de CDF : orbite, énergie, SCAO et thermique"),
        "summary": summary(
            "The orbit trade, array and battery sizing, attitude determination and control, and thermal control concepts.",
            "Le compromis d'orbite, le dimensionnement des panneaux et de la batterie, la détermination et le contrôle d'attitude, et les concepts de contrôle thermique.",
            [("Orbit selection trade", "Compromis de choix d'orbite"),
             ("Power, AOCS and thermal subsystem decisions, logged in the CDF",
              "Décisions des sous-systèmes énergie, SCAO et thermique, consignées dans la CDF")],
            oer("chapters 7, 9 and 10", "chapitres 7, 9 et 10")),
        "items": ["DECK:L07", "V-DES-05", "V-DES-07", "V-CON-02", "V-SCDF-19", "V-DES-09", "V-DES-08"],
    },
    {
        "name": ml("Week 2 · Day 4 — CDF Day 3: comms, structure, propulsion and trade studies",
                   "Semaine 2 · Jour 4 — Jour 3 de CDF : télécoms, structure, propulsion et études de compromis"),
        "summary": summary(
            "Link budget and band selection with its licensing consequences; structure and deployer fit; propulsion; two formal trades.",
            "Bilan de liaison et choix de bande avec ses conséquences de licence ; structure et compatibilité avec le déployeur ; propulsion ; deux compromis formels.",
            [("Link budget; ground-station planning; band selection and regulatory check",
              "Bilan de liaison ; planification des stations sol ; choix de bande et vérification réglementaire"),
             ("Structure, propulsion; link-band and propulsion trade studies; equipment selection",
              "Structure, propulsion ; études de compromis de bande et de propulsion ; sélection d'équipement")],
            oer("chapters 11, 12 and 13", "chapitres 11, 12 et 13")),
        "items": ["DECK:L08", "V-DES-10", "V-SCDF-03", "V-DES-14", "V-SCDF-13", "V-SCDF-09", "V-SCDF-10"],
    },
    {
        "name": ml("Week 2 · Day 5 — CDF Day 4: integration, V&V, cost, risk and the PDR",
                   "Semaine 2 · Jour 5 — Jour 4 de CDF : intégration, V et V, coûts, risques et PDR"),
        "summary": summary(
            "Close the interfaces, build the verification matrix, estimate cost, close the risk register, and present a PDR-style review.",
            "Fermer les interfaces, établir la matrice de vérification, estimer les coûts, clore le registre des risques et présenter une revue de type PDR.",
            [("Morning: interfaces, V&V matrix, test planning, cost, risk closure",
              "Matin : interfaces, matrice V et V, planification des essais, coûts, clôture des risques"),
             ("Afternoon: SpaceCDF optimiser; document export; PDR-style review",
              "Après-midi : optimiseur SpaceCDF ; export des documents ; revue de type PDR")],
            oer("chapters 14, 15 and 16", "chapitres 14, 15 et 16")),
        "items": ["DECK:L09", "V-SCDF-05", "V-SCDF-20", "V-DES-12", "V-DES-13", "V-DES-11", "V-SCDF-23",
                  "V-SCDF-15", "V-SCDF-24"],
    },
    {
        "name": ml("Week 3 · Day 1 — Operations concept: ground segment and mission control",
                   "Semaine 3 · Jour 1 — Concept d'opérations : segment sol et contrôle de mission"),
        "summary": summary(
            "Meet EOSAT-1, the mission control system and the mission planner; passes, packets and telecommands.",
            "Découvrir EOSAT-1, le système de contrôle de mission et le planificateur ; passages, paquets et télécommandes.",
            [("Ground segment architecture; MCS familiarisation; operations procedures",
              "Architecture du segment sol ; prise en main du MCS ; procédures d'exploitation"),
             ("Pass planning and scheduling; telecommand and telemetry definition; the Week 3 scenarios",
              "Planification et ordonnancement des passages ; définition des télécommandes et de la télémesure ; les scénarios de la semaine 3")],
            oer("chapters 17 and 18", "chapitres 17 et 18")),
        "items": ["DECK:L10", "V-CON-05", "V-CON-06", "V-PLN-01", "V-OPS-01", "W3DOCS:tools"],
    },
    {
        "name": ml("Week 3 · Day 2 — Mission operations training",
                   "Semaine 3 · Jour 2 — Formation à l'exploitation de mission"),
        "summary": summary(
            "Console positions, the voice loop, anomaly response and flight dynamics; dry runs of LEOP, nominal and contingency passes.",
            "Postes de console, boucle vocale, réponse aux anomalies et dynamique du vol ; répétitions de passages LEOP, nominaux et de contingence.",
            [("Positions and responsibilities; shift structure and handover; communication protocols",
              "Postes et responsabilités ; organisation des quarts et passation ; protocoles de communication"),
             ("Anomaly response; flight dynamics; dry runs", "Réponse aux anomalies ; dynamique du vol ; répétitions")],
            oer("chapters 18 and 19", "chapitres 18 et 19")),
        "items": ["DECK:L11", "V-OPS-03", "V-CON-04", "V-OPS-02", "W3DOCS:training"],
    },
    {
        "name": ml("Week 3 · Day 3 — Simulation day 1: LEOP and commissioning",
                   "Semaine 3 · Jour 3 — Jour de simulation 1 : LEOP et mise en service"),
        "summary": summary(
            "One team flies LEOP and commissioning while the other observes and critiques; anomalies are injected in real time.",
            "Une équipe mène la LEOP et la mise en service pendant que l'autre observe et critique ; des anomalies sont injectées en temps réel.",
            [("Full-day simulated LEOP and commissioning shift", "Quart simulé de LEOP et de mise en service sur toute la journée"),
             ("Structured observer critique; debrief and lessons learned", "Critique structurée des observateurs ; débriefing et leçons apprises")],
            oer("chapter 19", "chapitre 19")),
        "items": ["DECK:L12", "V-OPS-04", "V-OPS-05", "V-OPS-06", "V-OPS-07", "V-OPS-08", "V-OPS-09",
                  "V-OPS-12", "V-OPS-13", "W3DOCS:sim"],
    },
    {
        "name": ml("Week 3 · Day 4 — Simulation day 2: nominal operations and contingency",
                   "Semaine 3 · Jour 4 — Jour de simulation 2 : exploitation nominale et contingence"),
        "summary": summary(
            "Teams swap roles: routine passes, operator checks, and contingencies worked from symptom to ticket.",
            "Les équipes échangent les rôles : passages de routine, vérifications d'opérateur, et contingences traitées du symptôme à la fiche.",
            [("Full-day simulated nominal and contingency operations", "Exploitation nominale et de contingence simulée sur toute la journée"),
             ("Debrief", "Débriefing")],
            oer("chapter 19", "chapitre 19")),
        "items": ["DECK:L13", "V-OPS-10", "V-OPS-11"],
    },
    {
        "name": ml("Week 3 · Day 5 — Debrief, synthesis and pathways",
                   "Semaine 3 · Jour 5 — Débriefing, synthèse et parcours"),
        "summary": summary(
            "A structured debrief led by the student Flight Directors, course synthesis, pathways into the sector, and the final mission review.",
            "Un débriefing structuré mené par les directeurs de vol étudiants, la synthèse du cours, les parcours dans le secteur, et la revue de mission finale.",
            [("Morning: debrief, observer presentations, lessons-learned synthesis",
              "Matin : débriefing, présentations des observateurs, synthèse des leçons apprises"),
             ("Afternoon: course synthesis, pathways, final mission review",
              "Après-midi : synthèse du cours, parcours, revue de mission finale")],
            oer("Part IV, the engineering position reference", "partie IV, la référence des postes d'ingénierie")),
        "items": ["DECK:L14"],
    },
]


# ── The 12-week term (design/docs/orbit_north/syllabus_12week_en.md) ─────────────────
# The intensive's twelve days map one to one onto the term's twelve weeks: introduction
# weeks 1-2 (the CDF opens in the week 2 studio), design to the PDR in week 7, operations
# training weeks 8-9, simulations weeks 10-11, the review of the whole mission in week 12.
# Same items, same order (video/course_order.yaml); the agenda reads lecture and studio.
LAYOUT = os.environ.get("C2O_COURSE_LAYOUT", "term")      # "term" (12 weeks) or "intensive" (3 weeks)


def _lec(en, fr_):
    return ("Lecture and seminar: " + en, "Cours et séminaire : " + fr_)


def _stu(en, fr_):
    return ("Studio: " + en, "Atelier : " + fr_)


TERM = [
    ("Week 1 — Introduction: Canada in space and the concurrent design method",
     "Semaine 1 — Introduction : le Canada dans l'espace et la méthode de conception concourante",
     [_lec("L01 Canada in space and course onboarding; teams and roles",
           "L01 Le Canada dans l'espace et accueil du cours ; équipes et rôles"),
      _stu("L02 the concurrent design method; SpaceCDF accounts and tour; teams open a mission file and draft a problem statement",
           "L02 la méthode de conception concourante ; comptes et visite de SpaceCDF ; les équipes ouvrent un dossier de mission et rédigent un énoncé du problème")]),
    ("Week 2 — From need to concept: the CDF opens, and the informal MCR",
     "Semaine 2 — Du besoin au concept : le CDF s'ouvre, et la MCR informelle",
     [_lec("L03 from need to concept: problem statements, stakeholders, measures, trade studies, ConOps",
           "L03 du besoin au concept : énoncés de problème, parties prenantes, mesures, études de compromis, ConOps"),
      _stu("the CDF opens: mission alternatives trade; ConOps v0; first parametric budgets; risk register; informal MCR in the last hour",
           "le CDF s'ouvre : étude des options de mission ; ConOps v0 ; premiers bilans paramétriques ; registre des risques ; MCR informelle pendant la dernière heure")]),
    ("Week 3 — Locking the concept, and the Canadian regulatory landscape",
     "Semaine 3 — Figer le concept, et le paysage réglementaire canadien",
     [_lec("L04 closing the MCR and locking the concept; L05 the Canadian regulatory landscape",
           "L04 clore la MCR et figer le concept ; L05 le paysage réglementaire canadien"),
      _stu("MCR actions closed; concept v1; top-level requirements; regulatory brief and draft ISED application (due at the end of week 4)",
           "actions de la MCR closes ; concept v1 ; exigences de haut niveau ; note réglementaire et ébauche de demande à ISDE (dues à la fin de la semaine 4)")]),
    ("Week 4 — CDF 1: the System-V, requirements and first budgets",
     "Semaine 4 — CDF 1 : le cycle en V, les exigences et les premiers bilans",
     [_lec("L06 the System-V, requirements and first budgets", "L06 le cycle en V, les exigences et les premiers bilans"),
      _stu("CDF 1: requirements baseline; function tree; first mass, power, data and link budgets",
           "CDF 1 : référentiel d'exigences ; arbre fonctionnel ; premiers bilans de masse, d'énergie, de données et de liaison")]),
    ("Week 5 — CDF 2: orbit, power, attitude and thermal",
     "Semaine 5 — CDF 2 : orbite, énergie, attitude et thermique",
     [_lec("L07 orbit, power, attitude and thermal", "L07 orbite, énergie, attitude et thermique"),
      _stu("CDF 2: orbit selection; power, AOCS and thermal decisions logged",
           "CDF 2 : choix d'orbite ; décisions d'énergie, de SCAO et de thermique consignées")]),
    ("Week 6 — CDF 3: communications, structure, propulsion and the formal trades",
     "Semaine 6 — CDF 3 : télécommunications, structure, propulsion et compromis formels",
     [_lec("L08 communications, structure, propulsion and the formal trades",
           "L08 télécommunications, structure, propulsion et compromis formels"),
      _stu("CDF 3: link budget and ground-station plan; link-band and propulsion trade studies; equipment selection",
           "CDF 3 : bilan de liaison et plan des stations sol ; compromis de bande et de propulsion ; sélection d'équipement"),
      ("The reading break follows this week.", "La semaine de lecture suit cette semaine.")]),
    ("Week 7 — CDF 4: integration, verification, cost and risk, and the PDR",
     "Semaine 7 — CDF 4 : intégration, vérification, coûts et risques, et la PDR",
     [_lec("L09 integration, verification, cost and risk", "L09 intégration, vérification, coûts et risques"),
      _stu("CDF 4: interface closure; V&V matrix; test plan; cost and bill of materials; risk closure; ECSS documents; then the PDR-style review",
           "CDF 4 : fermeture des interfaces ; matrice V et V ; plan d'essais ; coûts et nomenclature ; clôture des risques ; documents ECSS ; puis la revue de type PDR")]),
    ("Week 8 — Operations training 1: from design to operations",
     "Semaine 8 — Formation à l'exploitation 1 : de la conception à l'exploitation",
     [_lec("L10 from design to operations: EOSAT-1, passes, PUS services, a telecommand's life, the mission planner",
           "L10 de la conception à l'exploitation : EOSAT-1, passages, services PUS, la vie d'une télécommande, le planificateur de mission"),
      _stu("MCS familiarisation by position; telemetry, alarms and procedures; pass planning",
           "prise en main du MCS par poste ; télémesure, alarmes et procédures ; planification de passage")]),
    ("Week 9 — Operations training 2: the control room",
     "Semaine 9 — Formation à l'exploitation 2 : la salle de contrôle",
     [_lec("L11 the control room: positions, the voice loop, anomaly response, shift handover",
           "L11 la salle de contrôle : postes, boucle vocale, réponse aux anomalies, passation de quart"),
      _stu("voice-loop drills; dry runs of LEOP, nominal and contingency passes; operations training quiz",
           "exercices de boucle vocale ; répétitions de passages LEOP, nominaux et de contingence ; quiz de formation à l'exploitation")]),
    ("Week 10 — Simulation 1: LEOP and commissioning",
     "Semaine 10 — Simulation 1 : LEOP et mise en service",
     [("L12 briefing, then a 6-hour simulated LEOP and commissioning shift: one team operates, the other observes",
       "Briefing L12, puis un quart simulé de 6 heures de LEOP et de mise en service : une équipe exploite, l'autre observe"),
      ("Post-simulation debrief", "Débriefing après la simulation")]),
    ("Week 11 — Simulation 2: nominal operations and contingency",
     "Semaine 11 — Simulation 2 : exploitation nominale et contingence",
     [("L13 briefing, then a 6-hour simulated shift of nominal and contingency operations; the teams swap roles",
       "Briefing L13, puis un quart simulé de 6 heures d'exploitation nominale et de contingence ; les équipes échangent les rôles"),
      ("Post-simulation debrief", "Débriefing après la simulation")]),
    ("Week 12 — Review of the whole mission",
     "Semaine 12 — Revue de toute la mission",
     [_lec("L14 debrief led by the student Flight Directors; lessons learned; pathways into the sector",
           "L14 débriefing mené par les directeurs de vol étudiants ; leçons apprises ; parcours dans le secteur"),
      _stu("from the need to the last pass: the design decisions against what operations showed; observer presentations; final mission review",
           "du besoin au dernier passage : les décisions de conception face à ce que l'exploitation a montré ; présentations des observateurs ; revue finale de mission")]),
]

W3DOCS = {
    "tools": ("Week 3 handout · Student tool reference", "Document de la semaine 3 · Référence des outils",
              "The tools you will use on console: the mission control system, the mission planner and the procedure panel.",
              "Les outils que vous utiliserez à la console : le système de contrôle de mission, le planificateur et le panneau des procédures.",
              [("Student tool reference", "Référence des outils pour les étudiants", *w3("Student_Tool_Reference"))]),
    "training": ("Week 3 handouts · Training days", "Documents de la semaine 3 · Journées de formation",
                 "Handouts for the two operations training days.",
                 "Les documents des deux journées de formation à l'exploitation.",
                 [("Training day 1", "Journée de formation 1", *w3("Training_Day1")),
                  ("Training day 2", "Journée de formation 2", *w3("Training_Day2"))]),
    "sim": ("Week 3 handouts · Simulation days", "Documents de la semaine 3 · Journées de simulation",
            "Bring these to both simulation days: the procedure quick reference for operators, the peer-review worksheets for observers.",
            "Apportez-les aux deux journées de simulation : l'aide-mémoire des procédures pour les opérateurs, les feuilles d'évaluation par les pairs pour les observateurs.",
            [("Procedure quick reference", "Aide-mémoire des procédures", *w3("Student_Procedure_Quickref")),
             ("Peer-review worksheets", "Feuilles d'évaluation par les pairs", *w3("Peer_Review_Worksheets"))]),
}


def expand(token: str) -> dict:
    if token.startswith("DECK:"):
        return deck_item(token[5:])
    if token.startswith("W3DOCS:"):
        k = token[7:]
        ne, nf, ie, if_, docs = W3DOCS[k]
        if LAYOUT == "term":           # the operations weeks, not the intensive's week 3
            ne = ne.replace("Week 3 handouts", "Operations handouts").replace("Week 3 handout", "Operations handout")
            nf = nf.replace("Documents de la semaine 3", "Documents d'exploitation").replace(
                "Document de la semaine 3", "Document d'exploitation")
        return doc_list_item(ne, nf, ie, if_, docs, f"W3DOCS-{k}")
    raise ValueError(token)


def expand_all(token: str) -> list[dict]:
    if token.startswith("V-"):
        return video_items(token)
    return [expand(token)]


WELCOME_EN = """<p><strong>ORBIT NORTH</strong> is a three-week course in space mission design and operations: two weeks designing a CubeSat mission concurrently, then a week flying one, EOSAT-1, in a simulated mission control room.</p>
<p>This site holds the course material: lecture slides, short videos with practice questions, handouts and an open textbook, organised day by day. Switch between English and French with the language menu at the top of the page; everything here exists in both languages.</p>
<p><strong>Nothing on this site is graded, and there is nowhere to submit work.</strong> Graded deliverables go through the university's own systems. The team workspace at the end of the course is for preparing material your team chooses to share publicly.</p>"""

WELCOME_FR = """<p><strong>ORBIT NORTH</strong> est un cours de trois semaines en conception et exploitation de missions spatiales : deux semaines à concevoir une mission CubeSat en mode concurrent, puis une semaine à en piloter une, EOSAT-1, dans une salle de contrôle de mission simulée.</p>
<p>Ce site rassemble le matériel du cours : diapositives, courtes vidéos avec questions d'entraînement, documents et un manuel libre, organisés jour par jour. Passez de l'anglais au français avec le menu de langue en haut de la page ; tout le contenu existe dans les deux langues.</p>
<p><strong>Rien sur ce site n'est noté, et aucun travail n'y est remis.</strong> Les livrables notés passent par les systèmes de l'université. L'espace d'équipe, à la fin du cours, sert à préparer ce que votre équipe choisit de partager publiquement.</p>"""

WELCOME_TERM_EN = """<p><strong>ORBIT NORTH</strong> is a 12-week course in space mission design and operations: a week and a half of introduction, then designing a CubeSat mission concurrently until the preliminary design review in week 7, two weeks of operations training, two weeks flying one, EOSAT-1, in a simulated mission control room, and a final week reviewing the whole mission.</p>
<p>This site holds the course material: lecture slides, short videos with practice questions, handouts and an open textbook, organised week by week. Switch between English and French with the language menu at the top of the page; everything here exists in both languages.</p>
<p><strong>Nothing on this site is graded, and there is nowhere to submit work.</strong> Graded deliverables go through the university's own systems. The team workspace at the end of the course is for preparing material your team chooses to share publicly.</p>"""

WELCOME_TERM_FR = """<p><strong>ORBIT NORTH</strong> est un cours de 12 semaines en conception et exploitation de missions spatiales : une semaine et demie d'introduction, puis la conception concourante d'une mission CubeSat jusqu'à la revue de conception préliminaire en semaine 7, deux semaines de formation à l'exploitation, deux semaines à en piloter une, EOSAT-1, dans une salle de contrôle de mission simulée, et une dernière semaine de revue de toute la mission.</p>
<p>Ce site rassemble le matériel du cours : diapositives, courtes vidéos avec questions d'entraînement, documents et un manuel libre, organisés semaine par semaine. Passez de l'anglais au français avec le menu de langue en haut de la page ; tout le contenu existe dans les deux langues.</p>
<p><strong>Rien sur ce site n'est noté, et aucun travail n'y est remis.</strong> Les livrables notés passent par les systèmes de l'université. L'espace d'équipe, à la fin du cours, sert à préparer ce que votre équipe choisit de partager publiquement.</p>"""

VIDEO_HELP_EN = """<p>Each video comes in English and in French: open either one. The video pauses at a few questions: answer them to check your understanding, then carry on. At the end, press <strong>Submit</strong>: that marks the video as done and unlocks the next video or handout. Your answers are kept on this site only for that and for anonymous course statistics; they are never graded.</p>
<p>All videos are listed from the start so you can see what is coming. They open one after the other, in the order of the course; you can go at your own pace.</p>
<ul><li>Captions are on by default; use the CC button to turn them off.</li>
<li>Chapters (the bookmark button) jump to each step.</li>
<li>The video follows the course language: switch the site to French for the French version.</li></ul>"""

VIDEO_HELP_FR = """<p>Chaque vidéo existe en anglais et en français : ouvrez l'une ou l'autre. La vidéo s'arrête sur quelques questions : répondez pour vérifier votre compréhension, puis continuez. À la fin, appuyez sur <strong>Soumettre</strong> : la vidéo est alors terminée et la vidéo ou le document suivant se débloque. Vos réponses ne sont conservées sur ce site que pour cela et pour des statistiques anonymes du cours ; elles ne sont jamais notées.</p>
<p>Toutes les vidéos sont affichées dès le début pour que vous voyiez la suite. Elles s'ouvrent l'une après l'autre, dans l'ordre du cours ; vous avancez à votre rythme.</p>
<ul><li>Les sous-titres sont activés par défaut ; le bouton CC permet de les désactiver.</li>
<li>Les chapitres (bouton signet) mènent à chaque étape.</li>
<li>La vidéo suit la langue du cours : passez le site en français pour la version française.</li></ul>"""

WORKSPACE_EN = """<p>This is your team's space to work together on material you want to share publicly about your mission: a summary of the concept, figures, a short video, lessons learned.</p>
<ul><li>Use the <strong>team room</strong> forum to discuss and to share drafts.</li>
<li>Use the <strong>showcase drafts</strong> wiki to write the pages themselves: start a page with your team's name.</li>
<li>When your team agrees a draft is ready, tell the course team: they publish selected work on the public site.</li></ul>
<p><strong>Do not post graded work, marks, feedback from instructors, or anyone's personal information here.</strong> Share only what your whole team agrees to make public.</p>"""

WORKSPACE_FR = """<p>Voici l'espace où votre équipe travaille ensemble sur ce qu'elle veut partager publiquement à propos de sa mission : un résumé du concept, des figures, une courte vidéo, des leçons apprises.</p>
<ul><li>Utilisez le forum <strong>salle d'équipe</strong> pour discuter et partager des ébauches.</li>
<li>Utilisez le wiki <strong>ébauches de vitrine</strong> pour rédiger les pages elles-mêmes : commencez une page au nom de votre équipe.</li>
<li>Quand votre équipe juge une ébauche prête, prévenez l'équipe pédagogique : elle publie une sélection des travaux sur le site public.</li></ul>
<p><strong>N'y publiez ni travaux notés, ni notes, ni rétroaction des enseignants, ni renseignements personnels.</strong> Ne partagez que ce que toute l'équipe accepte de rendre public.</p>"""



# ── Assignments, rubrics and AI use (assessments.yaml, mse_clo_rubrics.yaml) ─────────────
OUTCOMES = REPO / "design/configs/outcomes"


def _yaml(path: Path):
    import yaml
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _lv(lang: str, n: int, rub: dict) -> str:
    return f"{n} · {rub['levels'][n][lang]}"


def rubric_table(codes: list[str], lang: str) -> str:
    """The CLO rubric rows an assessment is marked on, all five levels, target levels marked."""
    rub = _yaml(OUTCOMES / "mse_clo_rubrics.yaml")
    plos = _yaml(OUTCOMES / "orbit_north_outcomes.yaml")["plos"]
    head = ("Criterion (program outcome)" if lang == "en" else "Critère (résultat du programme)")
    cols = "".join(f'<th style="background:{c};color:#222">{esc(_lv(lang, n, rub))}</th>'
                   for n, c in zip(range(1, 6), ("#FFF9C4", "#C8E6C9", "#81D4FA", "#E1BEE7", "#F8BBD0")))
    rows = []
    for code in codes:
        c = rub["clos"][code]
        plo = c["plo"]
        plo_name = plos.get(plo, {}).get(lang, "")
        cells = "".join(
            f'<td style="{"outline:2px solid #8F001A;" if n in (3, 4) else ""}">{esc(c["levels"][n][lang] if lang == "en" else fr(c["levels"][n][lang]))}</td>'
            for n in range(1, 6))
        name = c["name"][lang] if lang == "en" else fr(c["name"][lang])
        desc = c["description"][lang] if lang == "en" else fr(c["description"][lang])
        rows.append(f'<tr><td><strong>{esc(code)} {esc(name)}</strong><br><span class="small">{esc(desc)}</span>'
                    f'<br><span class="small text-muted">→ {esc(plo)} {esc(plo_name)}</span></td>{cells}</tr>')
    tgt = _yaml(OUTCOMES / "orbit_north_outcomes.yaml")["targets"]
    note = (f'<p class="small">{esc(tgt["GNG3100"][lang] if lang == "en" else fr(tgt["GNG3100"][lang]))} '
            f'{esc(tgt["SYS5186"][lang] if lang == "en" else fr(tgt["SYS5186"][lang]))} '
            + ("Levels 3 and 4 are outlined." if lang == "en" else fr("Les niveaux 3 et 4 sont encadrés."))
            + "</p>")
    return (f'<div style="overflow-x:auto"><table class="table table-bordered small"><thead><tr><th>{esc(head)}</th>{cols}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>' + note)


def _cm_links(ids: list[str], lang: str, label) -> str:
    """Links to course items by idnumber; build_course.php resolves @@CM:id@@ to the URL."""
    out = []
    for i in ids:
        if i.startswith("V-"):
            sb = SB[i]
            t = tr(sb.title, lang)
            out.append(f'<li><a href="@@CM:{i}-{lang.upper()}@@">{esc(t if lang == "en" else fr(t))}</a></li>')
        else:
            out.append(f'<li><a href="@@CM:{i}@@">{esc(label(i, lang))}</a></li>')
    return "<ul>" + "".join(out) + "</ul>" if out else ""


HANDOUT_LABEL = {"W3DOCS-tools": ("Student tool reference", "Référence des outils"),
                 "W3DOCS-training": ("Training day handouts", "Documents des journées de formation"),
                 "W3DOCS-sim": ("Procedure quick reference and peer-review worksheets",
                                "Aide-mémoire des procédures et feuilles d'évaluation par les pairs")}


def assessment_items() -> list[dict]:
    spec = _yaml(Path(__file__).with_name("assessments.yaml"))
    oc = _yaml(OUTCOMES / "orbit_north_outcomes.yaml")
    rub = _yaml(OUTCOMES / "mse_clo_rubrics.yaml")
    T = {"en": {"week": "Week", "who": "Who", "weight": "Weight", "purpose": "Why", "produce": "What you produce",
                "steps": "How to do it", "help": "Videos and handouts that help", "rubric": "How it is marked",
                "rubric_small": "Marked by the instructors on its own answer key (no program rubric).",
                "ai": "AI use", "plo": "Program outcomes this assessment gives evidence for"},
         "fr": {"week": "Semaine", "who": "Qui", "weight": "Pondération", "purpose": "Pourquoi",
                "produce": "Ce que vous produisez", "steps": "Comment faire", "help": "Vidéos et documents utiles",
                "rubric": "Comment c'est évalué",
                "rubric_small": "Corrigé par l'équipe pédagogique selon son propre corrigé (sans grille du programme).",
                "ai": "Utilisation de l'IA", "plo": "Résultats du programme dont cette évaluation fournit la preuve"}}
    items = []
    # 1. AI use, 2. the rubric map, then one page per assessment
    items.append({"type": "page", "name": ml("Using generative AI: how to declare it", "Utiliser l'IA générative : comment le déclarer"),
                  "content": mlr(spec["ai_declaration"]["en"]
                                 + "<p>Declare AI use in every deliverable, in your logbooks when AI shaped a decision, "
                                   "and in the AI use field of every entry in the team documents library.</p>",
                                 fr(spec["ai_declaration"]["fr"])
                                 + fr("<p>Déclarez l'utilisation de l'IA dans chaque livrable, dans vos carnets de bord quand "
                                      "l'IA a influencé une décision, et dans le champ Utilisation de l'IA de chaque entrée "
                                      "de la bibliothèque des documents d'équipe.</p>")),
                  "files": [], "idnumber": "AI-USE"})
    def map_table(lang):
        h = ("Assessment", "Week", "GNG 3100", "SYS 5186", "Rubric criteria → program outcomes") if lang == "en" else \
            ("Évaluation", "Semaine", "GNG 3100", "SYS 5186", "Critères de la grille → résultats du programme")
        rows = []
        for aid, a in oc["assessments"].items():
            sa = spec["assessments"][aid]
            crit = "; ".join(f'{c} {rub["clos"][c]["name"][lang]} → {rub["clos"][c]["plo"]}' for c in a["rubrics"]) \
                if a.get("large") else (T[lang]["rubric_small"])
            nm = a[lang] if lang == "en" else fr(a[lang])
            rows.append(f'<tr><td><a href="@@CM:ASSESS-{aid}@@">{esc(nm)}</a></td><td>{esc(str(sa["week"]))}</td>'
                        f'<td>{a["weight"]["GNG3100"]} %</td><td>{a["weight"]["SYS5186"]} %</td>'
                        f'<td>{esc(crit if lang == "en" else fr(crit))}</td></tr>')
        intro = ("Every assessment, its weight, and the program rubric criteria the large ones are marked on. "
                 "Each criterion rolls up to a program learning outcome of the Master of Systems Engineering.") if lang == "en" else \
            fr("Chaque évaluation, sa pondération, et les critères de la grille du programme sur lesquels les grandes évaluations "
               "sont notées. Chaque critère se rattache à un résultat d'apprentissage du programme de maîtrise en ingénierie des systèmes.")
        return (p(esc(intro)) + '<div style="overflow-x:auto"><table class="table table-bordered small"><thead><tr>'
                + "".join(f"<th>{esc(x)}</th>" for x in h) + "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>")
    items.append({"type": "page", "name": ml("Assessments and the program rubrics", "Évaluations et grilles du programme"),
                  "content": mlr(map_table("en"), map_table("fr")), "files": [], "idnumber": "RUBRIC-MAP"})
    for aid, a in oc["assessments"].items():
        sa = spec["assessments"][aid]
        def page(lang):
            t = T[lang]
            f_ = (lambda x: x) if lang == "en" else fr
            meta = (f'<p><strong>{t["week"]}</strong> {esc(str(sa["week"]))} · <strong>{t["who"]}</strong> {esc(f_(sa["who"][lang]))}'
                    f' · <strong>{t["weight"]}</strong> GNG 3100 {a["weight"]["GNG3100"]} %, SYS 5186 {a["weight"]["SYS5186"]} %</p>')
            body = (meta + f"<h4>{t['purpose']}</h4>" + p(esc(f_(sa["purpose"][lang])))
                    + f"<h4>{t['produce']}</h4>" + p(esc(f_(sa["produce"][lang])))
                    + f"<h4>{t['steps']}</h4><ol>" + "".join(f"<li>{esc(f_(st[lang]))}</li>" for st in sa["steps"]) + "</ol>")
            help_ = _cm_links(list(sa.get("videos") or []) + list(sa.get("handouts") or []), lang,
                              lambda i, l: HANDOUT_LABEL[i][0 if l == "en" else 1])
            if help_:
                body += f"<h4>{t['help']}</h4>" + help_
            body += f"<h4>{t['rubric']}</h4>"
            if a.get("large"):
                plo = sorted({rub["clos"][c]["plo"] for c in a["rubrics"]})
                body += p(f"<strong>{t['plo']}</strong>: " + esc(", ".join(plo))) + rubric_table(a["rubrics"], lang)
            else:
                body += p(esc(t["rubric_small"]))
            body += f"<h4>{t['ai']}</h4>" + (spec["ai_declaration"][lang] if lang == "en" else fr(spec["ai_declaration"][lang]))
            body += spec["submit"][lang] if lang == "en" else fr(spec["submit"][lang])
            return body
        items.append({"type": "page", "name": ml(f"{aid} · {a['en']}", f"{aid} · {a['fr']}"),
                      "content": mlr(page("en"), page("fr")), "files": [], "idnumber": f"ASSESS-{aid}"})
    return items


# ── The project space (shared by every team) ─────────────────────────────────────────────
PROJECT_EN = """<p>One space for all the teams to share and work on what the mission produces: the documents SpaceCDF and the C2O tools export, the decisions your team takes, and drafts for the public site. Everyone can read everything; each team edits its own entries.</p>
<ul><li><strong>Team documents and decisions</strong>: add an entry for each document or decision. Upload the file exported from SpaceCDF or the C2O tools, say what it is and what was decided, and fill in <strong>AI use</strong> (write "none" if none was used).</li>
<li><strong>Team room</strong>: discuss, ask the other teams, share work in progress.</li>
<li><strong>Project wiki</strong>: write together, one page per team (start from the first page and link yours).</li>
<li>When your team agrees an entry can be shown publicly, tick <strong>Ready for the public site</strong>. The course team picks from these for the community site.</li></ul>
<p><strong>Nothing here is graded or submitted.</strong> Graded work goes to Brightspace. Do not post marks, instructor feedback or anyone's personal information.</p>"""
PROJECT_FR = """<p>Un espace commun à toutes les équipes pour partager et travailler ce que produit la mission : les documents qu'exportent SpaceCDF et les outils C2O, les décisions de votre équipe, et les ébauches pour le site public. Tout le monde peut tout lire ; chaque équipe modifie ses propres entrées.</p>
<ul><li><strong>Documents et décisions d'équipe</strong> : ajoutez une entrée pour chaque document ou décision. Déposez le fichier exporté de SpaceCDF ou des outils C2O, dites de quoi il s'agit et ce qui a été décidé, et remplissez <strong>Utilisation de l'IA</strong> (écrivez « aucune » s'il n'y en a pas eu).</li>
<li><strong>Salle d'équipe</strong> : discutez, interrogez les autres équipes, partagez le travail en cours.</li>
<li><strong>Wiki du projet</strong> : rédigez ensemble, une page par équipe (partez de la première page et ajoutez un lien vers la vôtre).</li>
<li>Quand votre équipe accepte qu'une entrée soit montrée publiquement, cochez <strong>Prête pour le site public</strong>. L'équipe pédagogique choisit parmi celles-ci pour le site communautaire.</li></ul>
<p><strong>Rien ici n'est noté ni remis.</strong> Les travaux notés vont dans Brightspace. N'y publiez ni notes, ni rétroaction des enseignants, ni renseignements personnels.</p>"""

KINDS = ["Decision record · Fiche de décision", "Trade study · Étude de compromis",
         "Review data pack · Dossier de revue", "Requirements · Exigences", "Budgets · Bilans",
         "Interface document (ICD) · Document d'interface (DCI)", "Concept of operations · Concept d'opérations",
         "Risk register · Registre des risques", "Licensing · Licences",
         "Operations record (pass plan, anomaly ticket, handover) · Trace d'exploitation (plan de passage, fiche d'anomalie, passation)",
         "Draft for the public site · Ébauche pour le site public", "Other · Autre"]
SOURCES = ["SpaceCDF export · Export SpaceCDF", "C2O mission control (MCS, planner) · Contrôle de mission C2O (MCS, planificateur)",
           "Simulator or logbook · Simulateur ou carnet de bord", "Made outside the tools · Fait hors des outils"]


def project_items() -> list[dict]:
    return [
        {"type": "page", "name": ml("How the project space works", "Fonctionnement de l'espace projet"),
         "content": mlh(PROJECT_EN, fr(PROJECT_FR)), "files": [], "idnumber": "WS-HELP"},
        {"type": "data", "name": ml("Team documents and decisions", "Documents et décisions d'équipe"),
         "intro": mlh(p(esc("Every team's documents and decisions, with the files from SpaceCDF and the C2O tools. "
                             "Fill in AI use for every entry.")),
                      p(esc(fr("Les documents et décisions de toutes les équipes, avec les fichiers de SpaceCDF et des "
                               "outils C2O. Remplissez Utilisation de l'IA pour chaque entrée.")))),
         "idnumber": "WS-DOCS",
         "fields": [
             {"type": "text", "name": "Team · Équipe", "description": "Your team's name · Le nom de votre équipe", "required": True},
             {"type": "text", "name": "Title · Titre", "description": "What the entry is · Ce qu'est l'entrée", "required": True},
             {"type": "menu", "name": "Kind · Type", "description": "Kind of document · Type de document", "required": True,
              "options": KINDS},
             {"type": "menu", "name": "Made with · Produit avec", "description": "Where it came from · D'où il vient",
              "required": False, "options": SOURCES},
             {"type": "file", "name": "File · Fichier", "description": "The exported or written file · Le fichier exporté ou rédigé",
              "required": False},
             {"type": "textarea", "name": "Summary or decision · Résumé ou décision",
              "description": "What it says; for a decision: the options, the choice and why · Ce qu'il dit ; pour une décision : les options, le choix et pourquoi",
              "required": True},
             {"type": "textarea", "name": "AI use · Utilisation de l'IA",
              "description": "Tools, for what, how you checked, what stayed yours; or 'none' · Outils, pour quoi, comment vous avez vérifié, ce qui reste à vous ; ou « aucune »",
              "required": True},
             {"type": "menu", "name": "Status · État", "description": "Draft, for team review or final · Ébauche, à revoir en équipe ou final",
              "required": False, "options": ["Draft · Ébauche", "For team review · À revoir en équipe", "Final · Final"]},
             {"type": "checkbox", "name": "Ready for the public site · Prête pour le site public",
              "description": "The whole team agrees it can be shown publicly · Toute l'équipe accepte qu'elle soit montrée publiquement",
              "required": False, "options": ["Yes · Oui"]},
         ]},
        {"type": "forum", "name": ml("Team room", "Salle d'équipe"),
         "intro": mlh(p(esc("Discuss, ask the other teams, share work in progress.")),
                      p(esc(fr("Discutez, interrogez les autres équipes, partagez le travail en cours.")))),
         "idnumber": "WS-FORUM"},
        {"type": "wiki", "name": ml("Project wiki", "Wiki du projet"),
         "intro": mlh(p(esc("One page per team: start from the first page and add a link to your team's page.")),
                      p(esc(fr("Une page par équipe : partez de la première page et ajoutez un lien vers celle de votre équipe.")))),
         "firstpage": "Teams / Équipes", "idnumber": "WS-WIKI"},
    ]


def apply_unlock_chain(sections: list[dict]) -> None:
    """Videos and handouts open one after the other in course order: each needs the previous
    video finished, in either language. Slides, assignments and references are always open."""
    prev: list[str] = []
    for s in sections:
        pending: list[str] = []
        for it in s["items"]:
            if it["type"] == "h5pactivity":
                if prev:
                    it["after_any"] = list(prev)
                pending.append(it["idnumber"])
                if it.get("lang") == "fr":            # the pair is complete: it is the new "previous"
                    prev, pending = pending, []
            elif str(it.get("idnumber", "")).startswith("W3DOCS-") and prev:
                it["after_any"] = list(prev)


def build() -> dict:
    general = [
        {"type": "page", "name": ml("Welcome", "Bienvenue"),
         "content": (mlh(WELCOME_TERM_EN, fr(WELCOME_TERM_FR)) if LAYOUT == "term"
                     else mlh(WELCOME_EN, fr(WELCOME_FR))), "files": [], "idnumber": "WELCOME"},
        {"type": "page", "name": ml("How the videos work", "Fonctionnement des vidéos"),
         "content": mlh(VIDEO_HELP_EN, fr(VIDEO_HELP_FR)), "files": [], "idnumber": "VIDEO-HELP"},
        doc_list_item("Syllabus", "Plan de cours",
                      "The course outline: outcomes, calendar and approach.",
                      "Le plan du cours : résultats d'apprentissage, calendrier et approche.",
                      [("ORBIT NORTH syllabus", "Plan de cours ORBIT NORTH",
                        PDF / ("ORBIT_NORTH_Syllabus_12wk_EN.pdf" if LAYOUT == "term" else "ORBIT_NORTH_Syllabus_EN.pdf"),
                        PDF / ("ORBIT_NORTH_Syllabus_12wk_FR.pdf" if LAYOUT == "term" else "ORBIT_NORTH_Syllabus_FR.pdf"))],
                      "SYLLABUS"),
    ]
    sections = [{"name": None, "summary": "", "items": general},
                {"name": ml("Assignments, rubrics and AI use", "Travaux, grilles et utilisation de l'IA"),
                 "summary": mlh(p(esc("What each assessment asks for, how to do it, the program rubric it is marked on, "
                                      "and how to declare AI use. Everything is submitted on Brightspace, not here.")),
                                p(esc(fr("Ce que demande chaque évaluation, comment la faire, la grille du programme qui sert "
                                         "à la noter, et comment déclarer l'utilisation de l'IA. Tout se remet dans "
                                         "Brightspace, pas ici.")))),
                 "items": assessment_items()}]
    for i, s in enumerate(SECTIONS):
        if LAYOUT == "term":
            name_en, name_fr, lines = TERM[i]
            sections.append({"name": ml(name_en, name_fr), "summary": s["summary"].render(lines),
                             "items": [x for t in s["items"] for x in expand_all(t)]})
        else:
            sections.append({"name": s["name"], "summary": s["summary"].render(),
                             "items": [x for t in s["items"] for x in expand_all(t)]})
    sections.append({
        "name": ml("Project space", "Espace projet"),
        "summary": mlh(p(esc("Shared by every team: documents, decisions and drafts for the public site. Nothing here is graded.")),
                       p(esc(fr("Commun à toutes les équipes : documents, décisions et ébauches pour le site public. Rien ici n'est noté.")))),
        "items": project_items(),
    })
    sections.append({
        "name": ml("Textbook, workbook and references", "Manuel, cahier et références"),
        "summary": "",
        "items": [
            doc_list_item("Open textbook · Concurrent Spacecraft Design", "Manuel libre · Concurrent Spacecraft Design",
                          "The course textbook, licensed CC BY 4.0. Each " + ("week" if LAYOUT == "term" else "day")
                          + " lists the chapters to read.",
                          "Le manuel du cours, sous licence CC BY 4.0. Chaque "
                          + ("semaine" if LAYOUT == "term" else "journée") + " indique les chapitres à lire.",
                          [("Concurrent Spacecraft Design (English)", "Concurrent Spacecraft Design (français)",
                            PDF / "Concurrent_Spacecraft_Design_OER.pdf", PDF / "Concurrent_Spacecraft_Design_OER_FR.pdf")],
                          "OER"),
            doc_list_item("Course workbook", "Cahier d'exercices du cours",
                          "Worked exercises and worksheets for the design and operations parts of the course. Use them to practise; they are not submitted here.",
                          "Exercices et feuilles de travail pour les parties conception et exploitation du cours. Utilisez-les pour vous exercer ; ils ne sont pas remis ici.",
                          [("SpaceCDF course workbook", "Cahier d'exercices SpaceCDF",
                            PDF / "en/SpaceCDF_Workbook.pdf", PDF / "fr/SpaceCDF_Workbook_FR.pdf")], "WORKBOOK"),
            doc_list_item("Course textbook with the operations part", "Manuel du cours avec la partie exploitation",
                          "The SpaceCDF course textbook, including Part 2 on CubeSat operations, the procedure catalogue and the telemetry reference.",
                          "Le manuel du cours SpaceCDF, y compris la partie 2 sur l'exploitation des CubeSats, le catalogue des procédures et la référence de télémesure.",
                          [("SpaceCDF course textbook", "Manuel du cours SpaceCDF",
                            PDF / "en/SpaceCDF_Textbook.pdf", PDF / "fr/SpaceCDF_Textbook_FR.pdf")], "TEXTBOOK"),
        ],
    })
    apply_unlock_chain(sections)
    return {
        "course": {"fullname": ml("ORBIT NORTH — Space mission design and operations",
                                  "ORBIT NORTH — Conception et exploitation de missions spatiales"),
                   "shortname": "ORBIT-NORTH",
                   "summary": mlh(p(esc("Design a CubeSat mission in a concurrent design facility, then fly one in a simulated mission control room. Bilingual, open material; nothing on this site is graded.")),
                                  p(esc(fr("Concevez une mission CubeSat dans une installation de conception concurrente, puis pilotez-en une dans une salle de contrôle de mission simulée. Matériel bilingue et ouvert ; rien sur ce site n'est noté."))))},
        "sections": sections,
    }


def bundle(m: dict, dest: Path) -> Path:
    """Everything the build needs in one folder to copy to the Moodle server: manifest.json,
    build_course.php and files/ (paths in the manifest relative to the folder)."""
    import shutil
    files = dest / "files"
    files.mkdir(parents=True, exist_ok=True)
    seen: dict[str, str] = {}
    for s in m["sections"]:
        for it in s["items"]:
            for f in it.get("files", []):
                src = Path(f["path"])
                if seen.setdefault(f["name"], str(src)) != str(src):
                    raise SystemExit(f"two different files named {f['name']}")
                tgt = files / f["name"]
                if not tgt.exists() or tgt.stat().st_size != src.stat().st_size:
                    shutil.copy2(src, tgt)
                f["path"] = f"files/{f['name']}"
    for old in files.iterdir():                       # drop files a previous bundle needed
        if old.name not in seen:
            old.unlink()
    shutil.copy2(Path(__file__).with_name("build_course.php"), dest / "build_course.php")
    out = dest / "manifest.json"
    out.write_text(json.dumps(m, ensure_ascii=False, indent=1))
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Write the course manifest (and optionally a bundle for the server).")
    ap.add_argument("--bundle", help="folder to gather manifest.json, build_course.php and every file into")
    a = ap.parse_args()
    m = build()
    if a.bundle:
        size = sum(Path(f["path"]).stat().st_size for s in m["sections"] for it in s["items"] for f in it.get("files", []))
        out = bundle(m, Path(a.bundle).expanduser().resolve())
        print(f"bundle {out.parent} ({size / 1e6:.0f} MB): copy it to the Moodle server and run build_course.php there")
        sys.exit(0)
    out = Path(os.environ.get("C2O_MANIFEST", Path(__file__).with_name("manifest.json")))
    out.write_text(json.dumps(m, ensure_ascii=False, indent=1))
    n = sum(len(s["items"]) for s in m["sections"])
    size = sum(Path(f["path"]).stat().st_size for s in m["sections"] for it in s["items"] for f in it.get("files", []))
    print(f"{len(m['sections'])} sections, {n} items, {size / 1e6:.0f} MB of files -> {out}")
