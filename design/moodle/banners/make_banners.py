"""Section banners for the ORBIT NORTH Moodle course (card course format).

Text-free so they serve both languages; only the week.day number appears.
Palette matches the lecture decks. Writes out/<nn>_<key>.png at 1200x675.

    python make_banners.py
"""
from __future__ import annotations

import math
from pathlib import Path

NIGHT, NIGHT2, SNOW, ORANGE, BLUE, ICE = "#0f1c2e", "#16273d", "#f5f3ee", "#d9682b", "#2f6f9f", "#a9c7de"
W, H = 1200, 675
OUT = Path(__file__).with_name("out")


def stars(seed: int, n: int = 40) -> str:
    s, out = seed, []
    for _ in range(n):
        s = (s * 1103515245 + 12345) % 2**31
        x = s % W
        s = (s * 1103515245 + 12345) % 2**31
        y = s % (H // 2)
        out.append(f'<circle cx="{x}" cy="{y}" r="{1 + s % 3 * 0.6:.1f}" fill="{SNOW}" opacity="0.5"/>')
    return "".join(out)


def sat(x, y, s=1.0, rot=0, wings=True) -> str:
    w = (f'<rect x="-95" y="-14" width="60" height="28" fill="{BLUE}" stroke="{ICE}" stroke-width="2"/>'
         f'<rect x="35" y="-14" width="60" height="28" fill="{BLUE}" stroke="{ICE}" stroke-width="2"/>'
         f'<line x1="-35" y1="0" x2="-20" y2="0" stroke="{ICE}" stroke-width="3"/>'
         f'<line x1="20" y1="0" x2="35" y2="0" stroke="{ICE}" stroke-width="3"/>') if wings else ""
    return (f'<g transform="translate({x},{y}) rotate({rot}) scale({s})">{w}'
            f'<rect x="-20" y="-26" width="40" height="52" rx="3" fill="{SNOW}"/>'
            f'<rect x="-12" y="-16" width="24" height="10" fill="{ORANGE}"/></g>')


def earth(cy=1150, r=700) -> str:
    return (f'<circle cx="{W/2}" cy="{cy}" r="{r}" fill="{BLUE}" opacity="0.55"/>'
            f'<circle cx="{W/2}" cy="{cy}" r="{r}" fill="none" stroke="{ICE}" stroke-width="3" opacity="0.7"/>')


def aurora() -> str:
    return "".join(
        f'<path d="M -50 {300 + 40*i} C 300 {150 + 30*i}, 700 {380 + 20*i}, 1250 {200 + 35*i}" '
        f'stroke="{c}" stroke-width="{38 - 8*i}" fill="none" opacity="{0.35 - 0.07*i}"/>'
        for i, c in enumerate([ORANGE, ICE, BLUE, ORANGE]))


def tag(label: str) -> str:
    return (f'<rect x="56" y="52" width="{30 + 30*len(label)}" height="76" rx="10" fill="{ORANGE}"/>'
            f'<text x="{71 + 15*len(label)}" y="106" text-anchor="middle" font-family="IBM Plex Sans, sans-serif" '
            f'font-weight="600" font-size="46" fill="{SNOW}">{label}</text>') if label else ""


def bg(seed: int, light=False) -> str:
    return (f'<rect width="{W}" height="{H}" fill="{SNOW if light else NIGHT}"/>' + ("" if light else stars(seed)))


# ---------------------------------------------------------------- motifs
def m_general():          # course banner: the name is the same in both languages
    title = (f'<text x="600" y="330" text-anchor="middle" font-family="IBM Plex Sans, sans-serif" font-weight="600" '
             f'font-size="104" letter-spacing="10" fill="{SNOW}">ORBIT NORTH</text>'
             f'<rect x="420" y="362" width="360" height="8" rx="4" fill="{ORANGE}"/>')
    return bg(1) + aurora() + earth(1250, 760) + title + sat(990, 150, 0.7, -12)


def m_canada():           # 1.1 Canada in space: aurora over the north, a satellite
    return bg(2) + aurora() + earth(1200, 760) + sat(300, 210, 0.9, 10)


def m_concept():          # 1.2 need -> concept -> ConOps: three linked nodes
    n = [(300, 360), (600, 250), (900, 400)]
    lines = "".join(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{ICE}" stroke-width="6" '
                    f'stroke-dasharray="14 10"/>' for a, b in zip(n, n[1:]))
    nodes = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}"/>'
                    for (x, y), r, c in zip(n, (60, 80, 70), (BLUE, ORANGE, BLUE)))
    return bg(3) + lines + nodes + sat(900, 400, 0.6)


def m_regulatory():       # 2.1 rules: stacked documents and an orbit ring
    docs = "".join(f'<rect x="{430 + 26*i}" y="{170 + 22*i}" width="300" height="380" rx="10" fill="{SNOW}" '
                   f'stroke="{ICE}" stroke-width="3" opacity="{0.6 + 0.2*i}"/>' for i in range(3))
    lines = "".join(f'<rect x="520" y="{290 + 40*k}" width="{200 - 30*(k % 2)}" height="12" rx="6" fill="{ICE}"/>'
                    for k in range(5))
    seal = f'<circle cx="770" cy="520" r="52" fill="{ORANGE}"/><circle cx="770" cy="520" r="34" fill="none" stroke="{SNOW}" stroke-width="5"/>'
    ring = f'<ellipse cx="600" cy="370" rx="470" ry="150" fill="none" stroke="{BLUE}" stroke-width="5" transform="rotate(-12 600 370)"/>'
    return bg(4) + ring + docs + lines + seal


def m_systemv():          # 2.2 the System-V
    L = [(250, 170), (380, 330), (510, 490)]
    R = [(950, 170), (820, 330), (690, 490)]
    path = f'M {L[0][0]} {L[0][1]} L 600 580 L {R[0][0]} {R[0][1]}'
    links = "".join(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{ICE}" stroke-width="3" '
                    f'stroke-dasharray="8 10"/>' for a, b in zip(L, R))
    dots = "".join(f'<circle cx="{x}" cy="{y}" r="26" fill="{c}"/>' for (x, y), c in
                   [(p, ORANGE) for p in L] + [(p, BLUE) for p in R])
    return bg(5) + links + f'<path d="{path}" stroke="{SNOW}" stroke-width="10" fill="none"/>' + dots


def m_orbit_power():      # 2.3 orbit, power, attitude, thermal: Sun, eclipse arc, winged spacecraft
    cx, cy = 230, 300
    sun = f'<circle cx="{cx}" cy="{cy}" r="70" fill="{ORANGE}"/>' + "".join(
        f'<line x1="{cx + 90*math.cos(a)}" y1="{cy + 90*math.sin(a)}" x2="{cx + 120*math.cos(a)}" '
        f'y2="{cy + 120*math.sin(a)}" stroke="{ORANGE}" stroke-width="6"/>' for a in [k*math.pi/6 for k in range(12)])
    orbit = f'<ellipse cx="640" cy="560" rx="520" ry="200" fill="none" stroke="{ICE}" stroke-width="4" stroke-dasharray="16 12"/>'
    shadow = f'<path d="M 900 470 L 1200 420 L 1200 700 L 900 700 Z" fill="#000" opacity="0.35"/>'
    return bg(6) + sun + earth(980, 420) + shadow + orbit + sat(640, 360, 1.1, -8)


def m_comms():            # 2.4 comms, structure, propulsion: dish, waves, spacecraft
    dish = (f'<path d="M 170 560 Q 300 400 430 560 Z" fill="{SNOW}"/>'
            f'<line x1="300" y1="520" x2="360" y2="440" stroke="{SNOW}" stroke-width="8"/>'
            f'<rect x="270" y="560" width="60" height="70" fill="{ICE}"/>')
    waves = "".join(f'<path d="M {470 + 70*i} {420 - 50*i} q 40 -40 0 -90" stroke="{ORANGE}" stroke-width="8" '
                    f'fill="none" opacity="{1 - 0.2*i}" transform="rotate(-35 {470 + 70*i} {420 - 50*i})"/>' for i in range(4))
    plume = f'<path d="M 860 220 L 990 180 L 990 260 Z" fill="{ORANGE}" opacity="0.6"/>'
    return bg(7) + dish + waves + plume + sat(840, 220, 1.0, 0)


def m_integration():      # 2.5 integration, V&V, PDR: an N-squared grid
    g = []
    n, s, x0, y0 = 6, 80, 360, 110
    for i in range(n):
        for j in range(n):
            if i == j:
                c, o = ORANGE, 1
            elif (i * 7 + j * 3) % 4 == 0:
                c, o = ICE, 0.9
            else:
                c, o = BLUE, 0.35
            g.append(f'<rect x="{x0 + j*s}" y="{y0 + i*s}" width="{s - 8}" height="{s - 8}" rx="6" fill="{c}" opacity="{o}"/>')
    check = f'<path d="M 920 470 l 50 50 l 100 -110" stroke="{SNOW}" stroke-width="18" fill="none" stroke-linecap="round"/>'
    return bg(8) + "".join(g) + check


def m_ground():           # 3.1 ground segment: station under a pass arc
    arc = f'<path d="M 80 600 Q 600 -80 1120 600" stroke="{ICE}" stroke-width="5" fill="none" stroke-dasharray="18 12"/>'
    dish = (f'<path d="M 470 560 Q 600 420 730 560 Z" fill="{SNOW}" transform="rotate(-20 600 560)"/>'
            f'<rect x="575" y="560" width="50" height="80" fill="{ICE}"/>')
    ground = f'<rect y="630" width="{W}" height="45" fill="{BLUE}" opacity="0.6"/>'
    beam = f'<path d="M 560 470 L 790 230 L 830 270 Z" fill="{ORANGE}" opacity="0.35"/>'
    return bg(9) + arc + ground + beam + dish + sat(820, 240, 0.8, -25)


def m_control_room():     # 3.2 control room: a row of consoles with telemetry
    out = []
    for k in range(4):
        x = 110 + k * 260
        out.append(f'<rect x="{x}" y="230" width="220" height="150" rx="10" fill="{NIGHT2}" stroke="{ICE}" stroke-width="3"/>')
        pts = " ".join(f"{x + 15 + t*19},{320 - 35*math.sin((t + k*2)/1.6) - (25 if (k == 2 and t > 7) else 0)}" for t in range(11))
        out.append(f'<polyline points="{pts}" stroke="{ORANGE if k == 2 else ICE}" stroke-width="4" fill="none"/>')
        out.append(f'<rect x="{x + 60}" y="380" width="100" height="18" fill="{ICE}" opacity="0.6"/>')
    desk = f'<rect x="60" y="398" width="1080" height="40" rx="8" fill="{BLUE}"/>'
    loop = "".join(f'<path d="M {600 - 60 - 40*i} 560 q {60 + 40*i} -{50 + 30*i} {120 + 80*i} 0" stroke="{SNOW}" '
                   f'stroke-width="5" fill="none" opacity="{0.8 - 0.2*i}"/>' for i in range(3))
    return bg(10) + "".join(out) + desk + loop


def m_leop():             # 3.3 LEOP and commissioning: detumble spiral, wings opening, first light
    spiral = " ".join(f"{400 + (8 + 0.9*t)*math.cos(t/9)},{300 + (8 + 0.9*t)*math.sin(t/9)}" for t in range(160))
    light = f'<path d="M 760 380 L 640 650 L 900 650 Z" fill="{ORANGE}" opacity="0.3"/>'
    return (bg(11) + earth(1250, 700) + f'<polyline points="{spiral}" stroke="{ICE}" stroke-width="4" fill="none" opacity="0.7"/>'
            + sat(420, 340, 0.7, 35, wings=False) + light + sat(780, 330, 1.0, 0))


def m_nominal():          # 3.4 nominal and contingency: trend line crossing a limit
    limit = f'<line x1="80" y1="250" x2="1120" y2="250" stroke="{ORANGE}" stroke-width="4" stroke-dasharray="20 12"/>'
    pts = " ".join(f"{80 + t*26},{430 - 60*math.sin(t/4) - (0 if t < 24 else (t - 24)*20)}" for t in range(41))
    alarm = f'<circle cx="1010" cy="210" r="34" fill="{ORANGE}"/><rect x="1004" y="186" width="12" height="30" fill="{NIGHT}"/><circle cx="1010" cy="228" r="6" fill="{NIGHT}"/>'
    band = f'<rect x="80" y="250" width="1040" height="300" fill="{BLUE}" opacity="0.18"/>'
    return bg(12) + band + limit + f'<polyline points="{pts}" stroke="{ICE}" stroke-width="7" fill="none"/>' + alarm


def m_debrief():          # 3.5 debrief and pathways: paths fanning out to stars
    paths = "".join(f'<path d="M 600 640 C 600 450, {200 + 200*k} 380, {200 + 200*k} {160 + (k % 2)*60}" '
                    f'stroke="{ORANGE if k == 2 else ICE}" stroke-width="6" fill="none"/>'
                    f'<circle cx="{200 + 200*k}" cy="{160 + (k % 2)*60}" r="20" fill="{ORANGE if k == 2 else SNOW}"/>'
                    for k in range(5))
    return bg(13) + paths + f'<circle cx="600" cy="640" r="34" fill="{BLUE}"/>'


def m_workspace():        # team workspace: overlapping circles
    c = "".join(f'<circle cx="{x}" cy="{y}" r="170" fill="{col}" opacity="0.55"/>'
                for x, y, col in [(470, 300, BLUE), (730, 300, ORANGE), (600, 470, ICE)])
    return bg(14) + c + sat(600, 360, 0.6)


def m_references():       # textbook and references: a shelf of books
    books = []
    x = 180
    for k, (w, h, col) in enumerate([(70, 380, BLUE), (90, 420, ORANGE), (60, 340, ICE), (110, 400, SNOW),
                                    (75, 360, BLUE), (95, 430, ORANGE), (65, 330, ICE), (85, 390, BLUE)]):
        books.append(f'<rect x="{x}" y="{560 - h}" width="{w}" height="{h}" rx="6" fill="{col}"/>'
                     f'<rect x="{x + 12}" y="{600 - h}" width="{w - 24}" height="10" fill="{NIGHT}" opacity="0.4"/>')
        x += w + 14
    return bg(15) + "".join(books) + f'<rect x="120" y="560" width="960" height="24" rx="6" fill="{ICE}"/>'


BANNERS = [
    ("00_general", "", m_general), ("01_w1d1", "1.1", m_canada), ("02_w1d2", "1.2", m_concept),
    ("03_w2d1", "2.1", m_regulatory), ("04_w2d2", "2.2", m_systemv), ("05_w2d3", "2.3", m_orbit_power),
    ("06_w2d4", "2.4", m_comms), ("07_w2d5", "2.5", m_integration), ("08_w3d1", "3.1", m_ground),
    ("09_w3d2", "3.2", m_control_room), ("10_w3d3", "3.3", m_leop), ("11_w3d4", "3.4", m_nominal),
    ("12_w3d5", "3.5", m_debrief), ("13_workspace", "", m_workspace), ("14_references", "", m_references),
]


def main() -> None:
    from playwright.sync_api import sync_playwright
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        for name, label, fn in BANNERS:
            svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{fn()}{tag(label)}</svg>'
            (OUT / f"{name}.svg").write_text(svg)
            pg.set_content(f'<html><body style="margin:0">{svg}</body></html>')
            pg.screenshot(path=str(OUT / f"{name}.png"), clip={"x": 0, "y": 0, "width": W, "height": H})
        b.close()
    print("wrote", len(BANNERS), "banners to", OUT)


if __name__ == "__main__":
    main()
