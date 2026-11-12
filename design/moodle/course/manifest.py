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


def p(t: str) -> str:
    return f"<p>{t}</p>"


SB = {sb.id: sb for sb in storyboard.all_storyboards()}

PRACTICE = ("Questions in the video are for practice. Your answers are not recorded or graded.",
            "Les questions de la vidéo servent à s'exercer. Vos réponses ne sont ni enregistrées ni notées.")


def video_item(vid: str) -> dict:
    sb = SB[vid]
    slug = sb.slug
    files, parts = [], {}
    for lang in ("en", "fr"):
        pkg = VIDEOS / slug / f"{slug}.{lang}.h5p"
        assert pkg.exists(), pkg
        files.append({"name": pkg.name, "path": str(pkg)})
        summ = tr(sb.raw.get("summary") or {}, lang) or ""
        summ = fr(summ) if lang == "fr" else summ
        note = PRACTICE[0] if lang == "en" else fr(PRACTICE[1])
        parts[lang] = (p(esc(summ))
                       + f'<div class="h5p-placeholder" contenteditable="false">@@PLUGINFILE@@/{pkg.name}</div>'
                       + f'<p class="small text-muted">{esc(note)}</p>')
    name = ml("Video · " + tr(sb.title, "en"), "Vidéo · " + tr(sb.title, "fr"))
    return {"type": "page", "name": name, "content": mlh(parts["en"], parts["fr"]), "files": files,
            "idnumber": vid}


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


def summary(theme_en, theme_fr, lines, reading):
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
        return doc_list_item(ne, nf, ie, if_, docs, f"W3DOCS-{k}")
    return video_item(token)


WELCOME_EN = """<p><strong>ORBIT NORTH</strong> is a three-week course in space mission design and operations: two weeks designing a CubeSat mission concurrently, then a week flying one, EOSAT-1, in a simulated mission control room.</p>
<p>This site holds the course material: lecture slides, short videos with practice questions, handouts and an open textbook, organised day by day. Switch between English and French with the language menu at the top of the page; everything here exists in both languages.</p>
<p><strong>Nothing on this site is graded, and there is nowhere to submit work.</strong> Graded deliverables go through the university's own systems. The team workspace at the end of the course is for preparing material your team chooses to share publicly.</p>"""

WELCOME_FR = """<p><strong>ORBIT NORTH</strong> est un cours de trois semaines en conception et exploitation de missions spatiales : deux semaines à concevoir une mission CubeSat en mode concurrent, puis une semaine à en piloter une, EOSAT-1, dans une salle de contrôle de mission simulée.</p>
<p>Ce site rassemble le matériel du cours : diapositives, courtes vidéos avec questions d'entraînement, documents et un manuel libre, organisés jour par jour. Passez de l'anglais au français avec le menu de langue en haut de la page ; tout le contenu existe dans les deux langues.</p>
<p><strong>Rien sur ce site n'est noté, et aucun travail n'y est remis.</strong> Les livrables notés passent par les systèmes de l'université. L'espace d'équipe, à la fin du cours, sert à préparer ce que votre équipe choisit de partager publiquement.</p>"""

VIDEO_HELP_EN = """<p>Each video page plays an interactive video. The video pauses at a few questions: answer them to check your understanding, then carry on. Your answers are not recorded or graded.</p>
<ul><li>Captions are on by default; use the CC button to turn them off.</li>
<li>Chapters (the bookmark button) jump to each step.</li>
<li>The video follows the course language: switch the site to French for the French version.</li></ul>"""

VIDEO_HELP_FR = """<p>Chaque page vidéo lit une vidéo interactive. La vidéo s'arrête sur quelques questions : répondez pour vérifier votre compréhension, puis continuez. Vos réponses ne sont ni enregistrées ni notées.</p>
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


def build() -> dict:
    general = [
        {"type": "page", "name": ml("Welcome", "Bienvenue"),
         "content": mlh(WELCOME_EN, fr(WELCOME_FR)), "files": [], "idnumber": "WELCOME"},
        {"type": "page", "name": ml("How the videos work", "Fonctionnement des vidéos"),
         "content": mlh(VIDEO_HELP_EN, fr(VIDEO_HELP_FR)), "files": [], "idnumber": "VIDEO-HELP"},
        doc_list_item("Syllabus", "Plan de cours",
                      "The course outline: outcomes, calendar and approach.",
                      "Le plan du cours : résultats d'apprentissage, calendrier et approche.",
                      [("ORBIT NORTH syllabus", "Plan de cours ORBIT NORTH",
                        PDF / "ORBIT_NORTH_Syllabus_EN.pdf", PDF / "ORBIT_NORTH_Syllabus_FR.pdf")], "SYLLABUS"),
    ]
    sections = [{"name": None, "summary": "", "items": general}]
    for s in SECTIONS:
        sections.append({"name": s["name"], "summary": s["summary"], "items": [expand(t) for t in s["items"]]})
    sections.append({
        "name": ml("Team workspace", "Espace d'équipe"),
        "summary": mlh(p(esc("A shared space for each team to prepare its public showcase. Nothing here is graded.")),
                       p(esc(fr("Un espace partagé où chaque équipe prépare sa vitrine publique. Rien ici n'est noté.")))),
        "items": [
            {"type": "page", "name": ml("How to use this space", "Comment utiliser cet espace"),
             "content": mlh(WORKSPACE_EN, fr(WORKSPACE_FR)), "files": [], "idnumber": "WS-HELP"},
            {"type": "forum", "name": ml("Team room", "Salle d'équipe"),
             "intro": mlh(p(esc("Discuss, share drafts and coordinate your showcase.")),
                          p(esc(fr("Discutez, partagez vos ébauches et coordonnez votre vitrine.")))),
             "idnumber": "WS-FORUM"},
            {"type": "wiki", "name": ml("Showcase drafts", "Ébauches de vitrine"),
             "intro": mlh(p(esc("One page per team: start from the first page and add a link to your team's page.")),
                          p(esc(fr("Une page par équipe : partez de la première page et ajoutez un lien vers celle de votre équipe.")))),
             "firstpage": "Showcase / Vitrine", "idnumber": "WS-WIKI"},
        ],
    })
    sections.append({
        "name": ml("Textbook, workbook and references", "Manuel, cahier et références"),
        "summary": "",
        "items": [
            doc_list_item("Open textbook · Concurrent Spacecraft Design", "Manuel libre · Concurrent Spacecraft Design",
                          "The course textbook, licensed CC BY 4.0. Each day lists the chapters to read.",
                          "Le manuel du cours, sous licence CC BY 4.0. Chaque journée indique les chapitres à lire.",
                          [("Concurrent Spacecraft Design (English)", "Concurrent Spacecraft Design (français)",
                            PDF / "Concurrent_Spacecraft_Design_OER.pdf", PDF / "Concurrent_Spacecraft_Design_OER_FR.pdf")],
                          "OER"),
            doc_list_item("Course workbook", "Cahier d'exercices du cours",
                          "Worked exercises and worksheets for the design days and the operations week. Use them to practise; they are not submitted here.",
                          "Exercices et feuilles de travail pour les journées de conception et la semaine d'exploitation. Utilisez-les pour vous exercer ; ils ne sont pas remis ici.",
                          [("SpaceCDF course workbook", "Cahier d'exercices SpaceCDF",
                            PDF / "en/SpaceCDF_Workbook.pdf", PDF / "fr/SpaceCDF_Workbook_FR.pdf")], "WORKBOOK"),
            doc_list_item("Course textbook with the operations part", "Manuel du cours avec la partie exploitation",
                          "The SpaceCDF course textbook, including Part 2 on CubeSat operations, the procedure catalogue and the telemetry reference.",
                          "Le manuel du cours SpaceCDF, y compris la partie 2 sur l'exploitation des CubeSats, le catalogue des procédures et la référence de télémesure.",
                          [("SpaceCDF course textbook", "Manuel du cours SpaceCDF",
                            PDF / "en/SpaceCDF_Textbook.pdf", PDF / "fr/SpaceCDF_Textbook_FR.pdf")], "TEXTBOOK"),
        ],
    })
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
