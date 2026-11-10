"""ORBIT NORTH recruitment poster, 12-week format, in English and French.

Two US-letter pages in the style of the summer-intensive poster, printed to PDF
with Playwright's Chromium.

    cd design/docs/orbit_north/poster
    npm install                        # fonts (SIL OFL), once
    python3 build_poster_12week.py     # -> ../../pdf/ORBIT_NORTH_Recruitment_12wk_{EN,FR}.pdf

The hero photograph (a mission control room) is not in the repository. Put it
next to this script as hero.jpg, or pass --photo PATH; without it the hero
panel is left as a plain dark field.
"""
from __future__ import annotations

import argparse
import base64
import html
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONTS = HERE / "node_modules" / "@fontsource"
OUT = HERE.parent.parent / "pdf"

T = {
    "en": {
        "lang": "en",
        "eyebrow": "Space mission design<br>and operations",
        "lede": "Design a CubeSat mission. Command a live mission-control simulation. Build a career in space — over one term.",
        "meta": "<b>Winter 2027</b> · University of Ottawa · 3 credits",
        "caption": "",
        "stats": [("12", "Weeks · one term"), ("1", "Mission · end to end"), ("2", "Codes · UG &amp; grad"),
                  ("0", "Prior space experience<br>needed")],
        "intro": "ORBIT NORTH takes you from the Canadian space sector and its regulations, through a complete "
                 "preliminary CubeSat design in a Concurrent Design Facility, to the seat of a mission-control "
                 "console — across a twelve-week term at the University of Ottawa. Built for students with the "
                 "drive to do something real.",
        "weeks_h": "Your 12 weeks",
        "weeks_h2": "Your 12 weeks (continued)",
        "parts": [
            ("Weeks 1 – 4", "Context", "The Canadian space landscape and your mission concept",
             "Start with how real missions are built: the Canadian space sector, the concurrent design method and "
             "the SpaceCDF platform. Move from a mission need to a first concept of operations, present it at an "
             "informal Mission Concept Review in Week 2, and lock the concept in Week 3. Week 4 covers Canadian "
             "regulation in depth — the Remote Sensing Space Systems Act, ISED spectrum licensing, export controls "
             "and debris mitigation — and ends with your team’s regulatory brief.",
             ["Canadian sector", "SpaceCDF", "ConOps", "MCR", "RSSSA · ISED"]),
            ("Weeks 5 – 9", "Design", "Concurrent Design Facility",
             "One design stage per week on the SpaceCDF platform. In interdisciplinary teams, take a discipline "
             "role and build a complete preliminary CubeSat mission: the requirements baseline; orbit, power, "
             "attitude and thermal; communications, structure and propulsion, with two formal trade studies; then "
             "integration, verification, cost and risk. The weekly rhythm leaves time for real analysis between "
             "studios. Week 9 is a Preliminary Design Review.",
             ["Requirements", "Subsystem design", "Trade studies", "Risk register", "PDR"]),
            ("Weeks 10 – 12", "Operations", "Live mission operations simulation",
             "Operations training in a mission control room: positions, the voice loop, pass planning, "
             "anomaly response and dry runs. Then two six-hour simulation blocks flying the EOSAT-1 Earth-observation "
             "satellite — launch, early operations and commissioning, then nominal operations with contingencies "
             "injected in real time. One team operates while another observes and documents, then the teams swap. "
             "The course closes with a structured debrief and a final mission review.",
             ["Mission control", "LEOP", "Anomaly response", "Mission debrief"]),
        ],
        "rhythm_h": "How the term works",
        "rhythm": [("1.5 h", "Lecture and seminar", "Each week, a short lecture on the week’s topic, then discussion."),
                   ("3 h", "Studio", "Team work in the design facility (Weeks 1–9) or the mission control room (Week 10)."),
                   ("6 h", "Simulation blocks", "Weeks 11 and 12: a full operations shift, run without a break.")],
        "rhythm_note": "In person, with a reading break after Week 6. Nothing to buy: the open textbook "
                       "<i>Concurrent Spacecraft Design</i>, the course videos, SpaceCDF and the simulator are all provided.",
        "outcomes_h": "What you’ll be able to do",
        "outcomes": ["Structure a space mission concept using ECSS and NASA frameworks",
                     "Design a CubeSat mission across all principal subsystems in a Concurrent Design Facility",
                     "Conduct stakeholder analysis grounded in the Canadian context",
                     "Navigate Canadian satellite licensing, export controls and RSSSA obligations",
                     "Execute spacecraft operations procedures in a mission control environment",
                     "Respond to anomalies and contingency scenarios in a live simulation"],
        "codes_h": "Two codes · differentiated outcomes",
        "codes": [("GNG 3100", "Topics in Engineering I", "Undergraduate. No prior space background required."),
                  ("SYS 5186", "Advanced Topics in Systems Engineering",
                   "Graduate. Additional outcomes in quantitative trade-off evaluation, sub-area leadership and "
                   "literature-grounded synthesis.")],
        "who_h": "Who’s involved",
        "who": ["University of Ottawa", "Faculty of Engineering · SEDTI"],
        "cta_eyebrow": "Interested? Get in touch.",
        "cta": "Express your interest →",
        "contact": "Dr Franz Newland · SEDTI, University of Ottawa<br>fnewland@uottawa.ca",
        "button": "Apply",
        "footer": "ORBIT NORTH · GNG 3100 / SYS 5186 · 12-week format · Winter 2027",
    },
    "fr": {
        "lang": "fr",
        "eyebrow": "Conception et exploitation<br>de missions spatiales",
        "lede": "Concevez une mission CubeSat. Commandez une simulation de contrôle de mission en direct. "
                "Lancez votre carrière dans le spatial — en une session.",
        "meta": "<b>Hiver 2027</b> · Université d’Ottawa · 3 crédits",
        "caption": "",
        "stats": [("12", "Semaines · une session"), ("1", "Mission · de bout en bout"),
                  ("2", "Codes · 1<sup>er</sup> cycle<br>et cycles sup."), ("0", "Expérience spatiale<br>préalable requise")],
        "intro": "ORBIT NORTH vous mène du secteur spatial canadien et de sa réglementation, à travers la conception "
                 "préliminaire complète d’un CubeSat dans un Centre de conception concourante, jusqu’au siège d’une "
                 "console de contrôle de mission — sur une session de douze semaines à l’Université d’Ottawa. "
                 "Conçu pour les étudiantes et étudiants qui veulent réaliser quelque chose de concret.",
        "weeks_h": "Vos 12 semaines",
        "weeks_h2": "Vos 12 semaines (suite)",
        "parts": [
            ("Semaines 1 à 4", "Contexte", "Le paysage spatial canadien et votre concept de mission",
             "Découvrez comment se construisent les vraies missions : le secteur spatial canadien, la méthode de "
             "conception concourante et la plateforme SpaceCDF. Passez d’un besoin de mission à un premier concept "
             "d’opérations, présentez-le à une revue de concept de mission informelle à la semaine 2, puis figez le "
             "concept à la semaine 3. La semaine 4 approfondit la réglementation canadienne — la Loi sur les "
             "systèmes de télédétection spatiale, les licences de spectre d’ISDE, le contrôle des exportations et "
             "l’atténuation des débris — et se termine par la note réglementaire de votre équipe.",
             ["Secteur canadien", "SpaceCDF", "ConOps", "MCR", "LSTS · ISDE"]),
            ("Semaines 5 à 9", "Conception", "Centre de conception concourante",
             "Une étape de conception par semaine sur la plateforme SpaceCDF. En équipes interdisciplinaires, "
             "assumez un rôle disciplinaire et construisez la conception préliminaire complète d’une mission "
             "CubeSat : la base d’exigences ; l’orbite, l’énergie, l’attitude et le thermique ; les "
             "télécommunications, la structure et la propulsion, avec deux études de compromis formelles ; puis "
             "l’intégration, la vérification, les coûts et les risques. Le rythme hebdomadaire laisse du temps pour "
             "une véritable analyse entre les ateliers. La semaine 9 est une revue de conception préliminaire.",
             ["Exigences", "Sous-systèmes", "Études de compromis", "Registre des risques", "PDR"]),
            ("Semaines 10 à 12", "Exploitation", "Simulation d’opérations de mission en direct",
             "Formation aux opérations en salle de contrôle de mission : postes, boucle vocale, "
             "planification des passages, réponse aux anomalies et répétitions. Puis deux blocs de simulation de "
             "six heures aux commandes du satellite d’observation de la Terre EOSAT-1 — lancement, premières "
             "opérations et mise en service, puis opérations nominales avec des contingences injectées en temps "
             "réel. Une équipe opère pendant qu’une autre observe et documente, puis les équipes échangent leurs "
             "rôles. Le cours se termine par un débriefing structuré et une revue finale de mission.",
             ["Contrôle de mission", "LEOP", "Réponse aux anomalies", "Débriefing"]),
        ],
        "rhythm_h": "Le déroulement de la session",
        "rhythm": [("1,5 h", "Cours et séminaire", "Chaque semaine, un court exposé sur le thème de la semaine, puis une discussion."),
                   ("3 h", "Atelier", "Travail d’équipe au centre de conception (semaines 1 à 9) ou en salle de contrôle (semaine 10)."),
                   ("6 h", "Blocs de simulation", "Semaines 11 et 12 : un quart d’exploitation complet, sans interruption.")],
        "rhythm_note": "En présentiel, avec une semaine de lecture après la semaine 6. Rien à acheter : le manuel libre "
                       "<i>Concurrent Spacecraft Design</i>, les vidéos du cours, SpaceCDF et le simulateur sont fournis.",
        "outcomes_h": "Ce que vous saurez faire",
        "outcomes": ["Structurer un concept de mission spatiale à l’aide des cadres de l’ECSS et de la NASA",
                     "Concevoir une mission CubeSat couvrant tous les principaux sous-systèmes dans un Centre de conception concourante",
                     "Mener une analyse des parties prenantes ancrée dans le contexte canadien",
                     "Maîtriser les licences satellitaires, le contrôle des exportations et les obligations de la LSTS au Canada",
                     "Exécuter des procédures d’opérations spatiales dans un environnement de contrôle de mission",
                     "Réagir aux anomalies et aux scénarios de contingence dans une simulation en direct"],
        "codes_h": "Deux codes · résultats différenciés",
        "codes": [("GNG 3100", "Sujets en génie I", "Premier cycle. Aucune formation préalable en spatial requise."),
                  ("SYS 5186", "Sujets avancés en ingénierie système",
                   "Cycles supérieurs. Résultats supplémentaires en évaluation quantitative des compromis, leadership "
                   "d’un sous-domaine et synthèse appuyée sur la littérature.")],
        "who_h": "Qui est impliqué",
        "who": ["Université d’Ottawa", "Faculté de génie · SEDTI"],
        "cta_eyebrow": "Intéressé·e ? Contactez-nous.",
        "cta": "Exprimez votre intérêt →",
        "contact": "D<sup>r</sup> Franz Newland · SEDTI, Université d’Ottawa<br>fnewland@uottawa.ca",
        "button": "S’inscrire",
        "footer": "ORBIT NORTH · GNG 3100 / SYS 5186 · format de 12 semaines · Hiver 2027",
    },
}


def font_faces() -> str:
    faces = [("Unbounded", "unbounded", [700, 800]), ("Manrope", "manrope", [400, 500, 600, 700, 800]),
             ("Space Mono", "space-mono", [400, 700])]
    out = []
    for fam, pkg, weights in faces:
        for w in weights:
            for sub in ("latin", "latin-ext"):
                f = FONTS / pkg / "files" / f"{pkg}-{sub}-{w}-normal.woff2"
                if f.exists():
                    out.append(f"@font-face{{font-family:'{fam}';font-weight:{w};font-style:normal;"
                               f"src:url('{f.as_uri()}') format('woff2');}}")
    return "\n".join(out)


CSS = """
@page { size: Letter; margin: 0; }
:root { --bg:#0a1421; --panel:#0c1b2c; --card:#11243a; --line:#1d3550; --cyan:#2de8f0; --text:#e8eef5;
        --muted:#9fb0c3; --chip:#154458; --amber:#e0874a; }
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { background: var(--bg); color: var(--text); font-family: 'Manrope', sans-serif; font-size: 9.6pt;
             line-height: 1.42; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.page { width: 8.5in; height: 11in; position: relative; overflow: hidden; page-break-after: always; background: var(--bg); }
.mono { font-family: 'Space Mono', monospace; text-transform: uppercase; letter-spacing: .16em; }
.hero { display: flex; height: 3.55in; }
.hero-text { width: 3.05in; background: var(--panel); padding: .42in .32in .3in .5in; position: relative; }
.hero-text:before { content: ""; position: absolute; left: .5in; top: .3in; width: .26in; height: 2px; background: var(--cyan); }
.eyebrow { color: var(--cyan); font-size: 6.6pt; font-weight: 700; margin-top: .06in; line-height: 1.5; }
h1 { font-family: 'Unbounded', sans-serif; font-weight: 800; font-size: 34pt; line-height: .98; letter-spacing: -.01em;
     margin: .1in 0 .14in; }
h1 span { display: block; } h1 .n { color: var(--cyan); }
.lede { font-size: 10.6pt; line-height: 1.36; color: #d7e0ea; }
.meta { margin-top: .14in; font-size: 6.4pt; color: var(--muted); line-height: 1.6; }
.meta b { color: var(--text); font-weight: 700; }
.hero-photo { flex: 1; background: #050b13 center/cover no-repeat; position: relative; }
.hero-photo:after { content: ""; position: absolute; inset: 0; background: linear-gradient(90deg, rgba(12,27,44,.55), rgba(12,27,44,0) 30%); }
.caption { position: absolute; right: .22in; bottom: .14in; text-align: right; font-size: 5.6pt; color: #c9d4df;
           z-index: 2; line-height: 1.5; text-shadow: 0 0 4px #000; }
.stats { display: flex; padding: .16in .5in .2in; border-bottom: 1px solid var(--line); background: var(--panel); }
.stat { flex: 1; }
.stat .num { font-family: 'Unbounded', sans-serif; font-weight: 700; font-size: 22pt; color: var(--cyan); line-height: 1.1; }
.stat .lbl { font-size: 5.8pt; color: var(--muted); margin-top: .05in; line-height: 1.5; }
.body { padding: .24in .5in 0; }
.intro { border-left: 2px solid var(--amber); padding: .02in 0 .02in .16in; font-size: 10.6pt; line-height: 1.45; color: #dbe3ec; }
.sec { color: var(--cyan); font-size: 6.6pt; font-weight: 700; padding-bottom: .07in; border-bottom: 1px solid var(--line);
       margin: .24in 0 .14in; }
.sec.first { margin-top: .3in; }
.part { display: flex; gap: .16in; margin-bottom: .2in; }
.part-label { width: 1.08in; padding-top: .08in; }
.part-label .wk { font-size: 6pt; color: var(--muted); }
.part-label .tag { font-family: 'Manrope'; font-weight: 700; font-size: 12.5pt; color: var(--cyan); margin-top: .03in;
                   line-height: 1.15; }
.card { flex: 1; background: var(--card); border: 1px solid var(--line); border-radius: 4px; padding: .13in .16in .12in; }
.card h3 { font-weight: 800; font-size: 11.4pt; margin-bottom: .05in; line-height: 1.25; }
.card p { font-size: 8.9pt; color: #c8d3de; line-height: 1.45; }
.chips { margin-top: .08in; display: flex; flex-wrap: wrap; gap: .05in; }
.chip { font-family: 'Space Mono'; font-size: 5.6pt; font-weight: 700; text-transform: uppercase; letter-spacing: .08em;
        color: var(--cyan); background: #0e2c3d; border: 1px solid var(--chip); border-radius: 9px; padding: .015in .09in; }
.pageno { position: absolute; right: .5in; bottom: .2in; font-size: 6pt; color: #5e7186; }
.corner { position: absolute; right: .5in; top: .32in; width: .1in; height: .1in; border-top: 1.5px solid var(--cyan);
          border-left: 1.5px solid var(--cyan); }
.rhythm { display: flex; gap: .12in; }
.rcard { flex: 1; background: var(--card); border: 1px solid var(--line); border-radius: 4px; padding: .1in .13in; }
.rcard .h { font-family: 'Unbounded'; font-weight: 700; font-size: 14pt; color: var(--cyan); line-height: 1.1; }
.rcard .t { font-weight: 800; font-size: 8.6pt; margin: .04in 0 .03in; }
.rcard p { font-size: 7.6pt; color: #c8d3de; line-height: 1.4; }
.rnote { font-size: 7.8pt; color: var(--muted); margin-top: .08in; }
.outcomes { display: grid; grid-template-columns: 1fr 1fr; column-gap: .3in; row-gap: .07in; }
.outcomes div { font-size: 8.2pt; color: #d3dce6; padding-left: .16in; position: relative; line-height: 1.38; }
.outcomes div:before { content: "→"; position: absolute; left: 0; color: var(--cyan); }
.codes { display: flex; gap: .14in; }
.code { flex: 1; background: var(--card); border: 1px solid var(--line); border-radius: 4px; padding: .11in .14in; }
.code .c { color: var(--cyan); font-size: 6.8pt; font-weight: 700; }
.code .n { font-weight: 800; font-size: 9.6pt; margin: .03in 0 .03in; }
.code p { font-size: 7.6pt; color: #b9c6d3; line-height: 1.4; }
.who { display: flex; gap: .08in; }
.pill { border: 1px solid #2a4a66; background: #102338; border-radius: 12px; padding: .03in .14in; font-size: 7.8pt; font-weight: 600; }
.cta { margin-top: .2in; border: 1.5px solid var(--cyan); border-radius: 6px; padding: .17in .2in; display: flex;
       align-items: center; background: #0d2131; }
.cta .l { flex: 1; }
.cta .e { color: var(--cyan); font-size: 6.4pt; font-weight: 700; }
.cta .big { font-weight: 800; font-size: 15pt; margin: .03in 0 .04in; }
.cta .who2 { font-size: 7.8pt; color: var(--muted); line-height: 1.5; }
.btn { background: var(--cyan); color: #04121d; font-family: 'Space Mono'; font-weight: 700; text-transform: uppercase;
       letter-spacing: .2em; font-size: 7.4pt; padding: .1in .3in; border-radius: 2px; }
.footer { position: absolute; left: .5in; right: .5in; bottom: .4in; border-top: 1px solid var(--line); padding-top: .09in;
          font-size: 5.8pt; color: #6f8296; }
"""


def chips(xs):
    return '<div class="chips">' + "".join(f'<span class="chip">{html.escape(x)}</span>' for x in xs) + "</div>"


def part(p):
    wk, tag, title, body, cs = p
    return (f'<div class="part"><div class="part-label"><div class="wk mono">{wk}</div><div class="tag">{tag}</div></div>'
            f'<div class="card"><h3>{title}</h3><p>{body}</p>{chips(cs)}</div></div>')


def fr_typo(s: str) -> str:
    """French spacing: no-break space before : and narrow no-break space before ; ? !"""
    s = re.sub(r" :", "\u00a0:", s)
    return re.sub(r" ([;?!])", "\u202f\\1", s)


def localise(t: dict) -> dict:
    if t["lang"] != "fr":
        return t
    def walk(o):
        if isinstance(o, str):
            return fr_typo(o)
        if isinstance(o, list):
            return [walk(x) for x in o]
        if isinstance(o, tuple):
            return tuple(walk(x) for x in o)
        if isinstance(o, dict):
            return {k: walk(v) for k, v in o.items()}
        return o
    return walk(t)


def page_html(t: dict, photo: str | None) -> str:
    t = localise(t)
    bg = f"background-image:url('{photo}')" if photo else ""
    caption = f'<div class="caption mono">{t["caption"]}</div>' if t["caption"] else ""
    stats = "".join(f'<div class="stat"><div class="num">{n}</div><div class="lbl mono">{l}</div></div>' for n, l in t["stats"])
    p1 = f"""
<section class="page">
  <div class="hero">
    <div class="hero-text">
      <div class="eyebrow mono">{t['eyebrow']}</div>
      <h1><span>ORBIT</span><span class="n">NORTH</span></h1>
      <div class="lede">{t['lede']}</div>
      <div class="meta mono">{t['meta']}</div>
    </div>
    <div class="hero-photo" style="{bg}">{caption}</div>
  </div>
  <div class="stats">{stats}</div>
  <div class="body">
    <div class="intro">{t['intro']}</div>
    <div class="sec mono first">{t['weeks_h']}</div>
    {part(t['parts'][0])}
    {part(t['parts'][1])}
  </div>
  <div class="pageno mono">01 / 02</div>
</section>"""
    rhythm = "".join(f'<div class="rcard"><div class="h">{h}</div><div class="t">{tt}</div><p>{d}</p></div>'
                     for h, tt, d in t["rhythm"])
    outs = "".join(f"<div>{o}</div>" for o in t["outcomes"])
    codes = "".join(f'<div class="code"><div class="c mono">{c}</div><div class="n">{n}</div><p>{d}</p></div>'
                    for c, n, d in t["codes"])
    who = "".join(f'<span class="pill">{w}</span>' for w in t["who"])
    p2 = f"""
<section class="page">
  <div class="corner"></div>
  <div class="body" style="padding-top:.36in">
    <div class="sec mono first" style="margin-top:0">{t['weeks_h2']}</div>
    {part(t['parts'][2])}
    <div class="sec mono">{t['rhythm_h']}</div>
    <div class="rhythm">{rhythm}</div>
    <div class="rnote">{t['rhythm_note']}</div>
    <div class="sec mono">{t['outcomes_h']}</div>
    <div class="outcomes">{outs}</div>
    <div class="sec mono">{t['codes_h']}</div>
    <div class="codes">{codes}</div>
    <div class="sec mono">{t['who_h']}</div>
    <div class="who">{who}</div>
    <div class="cta"><div class="l"><div class="e mono">{t['cta_eyebrow']}</div><div class="big">{t['cta']}</div>
      <div class="who2">{t['contact']}</div></div><div class="btn">{t['button']}</div></div>
  </div>
  <div class="footer mono">{t['footer']}</div>
  <div class="pageno mono">02 / 02</div>
</section>"""
    return (f'<!doctype html><html lang="{t["lang"]}"><head><meta charset="utf-8"><title>ORBIT NORTH</title>'
            f"<style>{font_faces()}{CSS}</style></head><body>{p1}{p2}</body></html>")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo", type=Path, default=HERE / "hero.jpg")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    photo = None
    if a.photo.exists():
        photo = "data:image/jpeg;base64," + base64.b64encode(a.photo.read_bytes()).decode()
    else:
        print(f"no photo at {a.photo}: hero panel left plain")
    if not FONTS.exists():
        raise SystemExit("fonts missing: run npm install in this folder")
    from playwright.sync_api import sync_playwright
    work = HERE / "out"
    work.mkdir(exist_ok=True)
    a.out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page()
        for lang, t in T.items():
            src = work / f"poster_12wk_{lang}.html"
            src.write_text(page_html(t, photo), encoding="utf-8")
            pg.goto(src.as_uri())
            pg.wait_for_load_state("networkidle")
            pg.evaluate("document.fonts.ready")
            pdf = a.out / f"ORBIT_NORTH_Recruitment_12wk_{lang.upper()}.pdf"
            pg.pdf(path=str(pdf), format="Letter", print_background=True, prefer_css_page_size=True)
            print(pdf)
        br.close()


if __name__ == "__main__":
    main()
