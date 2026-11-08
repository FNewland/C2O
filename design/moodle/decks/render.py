"""Render bilingual lecture decks (YAML) to Slides-format HTML and PDF.

Each deck is one YAML file in src/ holding both languages. A slide is a
1920x1080 <section> with inline styles only (the Slides artifact format),
so the same files can be published as editable decks. PDFs are printed
with Playwright, one page per slide.

    python render.py            # every deck
    python render.py L03 L07    # some decks
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "sim"))
from tools.i18n.typo import fix as fr_fix  # noqa: E402

ROOT = Path(__file__).parent
SRC, OUT = ROOT / "src", ROOT / "out"
FONTS = ROOT / "node_modules/@fontsource"

# Palette: arctic night and snow, aurora orange accent, glacier blue.
NIGHT, NIGHT2 = "#0f1c2e", "#16273d"
SNOW, SNOW2 = "#f5f3ee", "#e9e6de"
INK, MUTED = "#1b2430", "#5b6573"
ORANGE, BLUE, ICE = "#d9682b", "#2f6f9f", "#a9c7de"
SANS = "'IBM Plex Sans', 'Inter', sans-serif"
MONO = "'IBM Plex Mono', monospace"

COURSE = {"en": "ORBIT NORTH · GNG 3100 / SYS 5186", "fr": "ORBIT NORTH · GNG 3100 / SYS 5186"}


def tx(v, lang: str) -> str:
    """Pick a language from {en, fr} (or a plain string), escape, apply FR typography."""
    if isinstance(v, dict):
        v = v.get(lang) or v.get("en") or ""
    s = str(v)
    if lang == "fr":
        s = fr_fix(s, markdown=False)
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`(.+?)`", rf"<span style=\"font-family:{MONO};font-size:0.92em\">\1</span>", s)
    return s


def frame(sid: str, body: str, dark: bool, n: int, total: int, lang: str, notes: str = "") -> str:
    bg, fg = (NIGHT, SNOW) if dark else (SNOW, INK)
    foot_c = ICE if dark else MUTED
    footer = (f'<p style="position:absolute;left:128px;bottom:56px;width:1300px;font-size:24px;'
              f'color:{foot_c};letter-spacing:0.04em">{html.escape(COURSE[lang])}</p>'
              f'<p style="position:absolute;right:128px;bottom:56px;width:200px;text-align:right;'
              f'font-size:24px;color:{foot_c}">{n} / {total}</p>') if n > 1 else ""
    aside = f"<aside>{html.escape(notes)}</aside>" if notes else ""
    return (f'<section id="{sid}" style="background:{bg};color:{fg};font-family:{SANS};'
            f'padding:120px 128px 160px;display:flex;flex-direction:column;gap:44px">'
            f'{body}{footer}{aside}</section>')


def h2(t: str, dark=False) -> str:
    return (f'<h2 style="font-size:64px;font-weight:600;line-height:1.1;'
            f'color:{SNOW if dark else INK}">{t}</h2>')


def kicker(t: str, dark=False) -> str:
    return (f'<p style="font-size:26px;font-weight:600;letter-spacing:0.14em;'
            f'text-transform:uppercase;color:{ORANGE}">{t}</p>')


def render_slide(s: dict, lang: str, i: int, total: int, deck: dict) -> str:
    k = s.get("kind", "bullets")
    sid = s.get("id") or f"s{i:02d}"
    notes = tx(s.get("notes", ""), lang) if s.get("notes") else ""
    notes = html.unescape(re.sub("<[^>]+>", "", notes))
    if k == "cover":
        body = (f'<div style="position:absolute;left:0;top:0;width:24px;height:1080px;background:{ORANGE}"></div>'
                f'<div style="flex:1"></div>'
                f'{kicker(tx(deck["slot"], lang), True)}'
                f'<h1 style="font-size:96px;font-weight:600;line-height:1.05;width:1500px">{tx(deck["title"], lang)}</h1>'
                f'<p style="font-size:40px;line-height:1.3;color:{ICE};width:1400px">{tx(deck["subtitle"], lang)}</p>'
                f'<div style="flex:1"></div>'
                f'<p style="font-size:28px;color:{ICE}">{html.escape(COURSE[lang])}</p>')
        return frame(sid, body, True, i, total, lang, notes)
    dark = k in ("statement", "section")
    head = h2(tx(s["h"], lang), dark) if s.get("h") else ""
    kk = kicker(tx(s["k"], lang), dark) if s.get("k") else ""
    if k == "statement":
        body = (f'<div style="flex:1"></div>{kk}<p style="font-size:68px;font-weight:500;line-height:1.2;'
                f'width:1560px">{tx(s["text"], lang)}</p>'
                + (f'<p style="font-size:30px;color:{ICE};width:1500px">{tx(s["sub"], lang)}</p>' if s.get("sub") else "")
                + '<div style="flex:1"></div>')
    elif k in ("bullets", "objectives"):
        items = s["items"]
        chars = sum(len(tx(it, lang)) for it in items)
        size = 40 if len(items) <= 5 and chars < 480 else 35 if len(items) <= 7 and chars < 700 else 31
        tag = "ol" if k == "objectives" else "ul"
        lis = "".join(f'<li style="margin-bottom:{int(size*0.55)}px">{tx(it, lang)}</li>' for it in items)
        body = (f'{kk}{head}<{tag} style="font-size:{size}px;line-height:1.35;padding-left:44px;'
                f'width:1600px">{lis}</{tag}>')
    elif k == "cards":
        cards = s["cards"]
        w = {2: 790, 3: 520, 4: 385}[len(cards)]
        cs = "".join(
            f'<div style="width:{w}px;display:flex;flex-direction:column;gap:16px;background:#ffffff;'
            f'padding:36px;border-radius:14px;border-top:8px solid {ORANGE if j % 2 == 0 else BLUE}">'
            f'<h3 style="font-size:36px;font-weight:600;line-height:1.15">{tx(c["t"], lang)}</h3>'
            f'<p style="font-size:30px;line-height:1.4;color:{MUTED}">{tx(c["d"], lang)}</p></div>'
            for j, c in enumerate(cards))
        body = f'{kk}{head}<div style="display:flex;gap:28px;align-items:stretch">{cs}</div>'
    elif k == "table":
        rows = s["rows"]
        chars = sum(len(tx(c, lang)) for r in rows for c in r)
        size = 30 if len(rows) <= 6 and chars < 700 else 27 if len(rows) <= 8 and chars < 700 else 24
        th = "".join(f'<th style="text-align:left;padding:14px 18px;border-bottom:3px solid {INK};'
                     f'font-size:{size}px">{tx(c, lang)}</th>' for c in s["header"])
        trs = "".join("<tr>" + "".join(
            f'<td style="padding:12px 18px;border-bottom:1px solid #cfcac0;font-size:{size}px;'
            f'line-height:1.3;vertical-align:top{";font-weight:600" if ci == 0 else ""}">{tx(c, lang)}</td>'
            for ci, c in enumerate(r)) + "</tr>" for r in rows)
        body = f'{kk}{head}<table style="border-collapse:collapse;width:1664px"><tr>{th}</tr>{trs}</table>'
    elif k == "formulas":
        fs = "".join(
            f'<div style="display:flex;gap:40px;align-items:baseline;padding:14px 0;border-bottom:1px solid #cfcac0">'
            f'<p style="width:820px;font-family:{MONO};font-size:31px;color:{BLUE}">{tx(f["f"], lang)}</p>'
            f'<p style="width:800px;font-size:28px;line-height:1.35">{tx(f["d"], lang)}</p></div>'
            for f in s["items"])
        body = f'{kk}{head}<div style="display:flex;flex-direction:column">{fs}</div>'
    elif k == "steps":
        st = "".join(
            f'<div style="display:flex;gap:28px;align-items:flex-start">'
            f'<p style="width:72px;height:72px;border-radius:36px;background:{ORANGE};color:{SNOW};'
            f'font-size:34px;font-weight:600;text-align:center;line-height:72px">{j + 1}</p>'
            f'<p style="width:1500px;font-size:31px;line-height:1.35;padding-top:12px">{tx(x, lang)}</p></div>'
            for j, x in enumerate(s["items"]))
        body = f'{kk}{head}<div style="display:flex;flex-direction:column;gap:22px">{st}</div>'
    elif k == "split":
        left = "".join(f'<li style="margin-bottom:16px">{tx(x, lang)}</li>' for x in s["left"]["items"])
        right = "".join(f'<li style="margin-bottom:16px">{tx(x, lang)}</li>' for x in s["right"]["items"])
        col = (lambda t, lis, c: f'<div style="width:800px;display:flex;flex-direction:column;gap:18px">'
               f'<h3 style="font-size:36px;font-weight:600;color:{c}">{tx(t, lang)}</h3>'
               f'<ul style="font-size:33px;line-height:1.35;padding-left:40px">{lis}</ul></div>')
        body = (f'{kk}{head}<div style="display:flex;gap:64px">{col(s["left"]["t"], left, ORANGE)}'
                f'{col(s["right"]["t"], right, BLUE)}</div>')
    elif k == "close":
        lis = "".join(f'<li style="margin-bottom:18px">{tx(x, lang)}</li>' for x in s["items"])
        body = (f'{kicker(tx({"en": "Now, in the course", "fr": "Maintenant, dans le cours"}, lang))}'
                f'{head}<ul style="font-size:38px;line-height:1.35;padding-left:44px;width:1600px">{lis}</ul>')
    else:
        raise ValueError(f"unknown slide kind {k}")
    return frame(sid, body, dark, i, total, lang, notes)


FONT_CSS = "".join(
    f"@font-face{{font-family:'IBM Plex Sans';font-weight:{w};font-style:{st};"
    f"src:url('file://{FONTS}/ibm-plex-sans/files/ibm-plex-sans-latin-{w}-{st}.woff2') format('woff2')}}"
    for w, st in [(400, "normal"), (500, "normal"), (600, "normal"), (700, "normal"), (400, "italic")]
) + (f"@font-face{{font-family:'IBM Plex Mono';font-weight:400;"
     f"src:url('file://{FONTS}/ibm-plex-mono/files/ibm-plex-mono-latin-400-normal.woff2') format('woff2')}}")

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>{fonts}
*{{margin:0;padding:0;box-sizing:border-box}} @page{{size:1920px 1080px;margin:0}}
section{{width:1920px;height:1080px;position:relative;overflow:hidden;page-break-after:always}}
aside{{display:none}} h1,h2,h3,p,li{{text-wrap:pretty}}
</style></head><body>{body}</body></html>"""


def build(deck_id: str) -> list[Path]:
    deck = yaml.safe_load((SRC / f"{deck_id}.yaml").read_text())
    slides = [{"kind": "cover"}] + deck["slides"]
    outs = []
    for lang in ("en", "fr"):
        secs = [render_slide(s, lang, i, len(slides), deck) for i, s in enumerate(slides, 1)]
        d = OUT / f"{deck_id}.{lang}"
        (d / "project/slides").mkdir(parents=True, exist_ok=True)
        for s, sec in zip(slides, secs):
            sid = re.search(r'<section id="([^"]+)"', sec).group(1)
            (d / f"project/slides/{sid}.html").write_text(sec)
        page = OUT / f"{deck_id}.{lang}.html"
        page.write_text(PAGE.format(fonts=FONT_CSS, body="\n".join(secs)))
        outs.append(page)
    return outs


def to_pdf(pages: list[Path]) -> None:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1920, "height": 1080})
        for page in pages:
            pg.goto(f"file://{page}")
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(300)
            # overflow check: any element painted past the slide or the footer band
            bad = pg.evaluate("""() => [...document.querySelectorAll('section')].flatMap((s, i) => {
                const r = s.getBoundingClientRect(); const out = [];
                for (const e of s.querySelectorAll('h1,h2,h3,p,li,table,div')) {
                  if (e.style.position === 'absolute') continue;
                  const q = e.getBoundingClientRect();
                  if (q.bottom > r.top + 930 || q.right > r.left + 1800) out.push(i + 1);
                }
                return [...new Set(out)];
            })""")
            if bad:
                print(f"  ! {page.name}: content past the margins on slide(s) {sorted(set(bad))}")
            pg.pdf(path=str(page.with_suffix(".pdf")), width="1920px", height="1080px",
                   print_background=True, prefer_css_page_size=True)
        b.close()


if __name__ == "__main__":
    ids = sys.argv[1:] or sorted(p.stem for p in SRC.glob("*.yaml"))
    pages = [pg for d in ids for pg in build(d)]
    to_pdf(pages)
    print("rendered", ", ".join(ids))
