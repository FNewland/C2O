"""Title and closing cards, drawn with the C2O design system in Chromium.

The closing card is where the video hands over to the workbook: it lists the
worksheet parts and decisions the video prepares, in the viewer's language.
"""

from __future__ import annotations

import asyncio
import html
from pathlib import Path

from .storyboard import REPO, Storyboard, tr

DS = REPO / "sim/packages/smo-common/src/smo_common/ui/design-system.css"

L = {
    "en": {"week": "Week {n}", "next": "Now, in your workbook", "course": "ORBIT NORTH · SYS5186 / GNG3100",
           "licence": "C2O course video · CC0 1.0 (public domain) · narration: synthetic voice",
           "where": "Open it in the tool from the worksheet's “Where” links."},
    "fr": {"week": "Semaine {n}", "next": "Maintenant, dans votre cahier de travail", "course": "ORBIT NORTH · SYS5186 / GNG3100",
           "licence": "Vidéo de cours C2O · CC0 1.0 (domaine public) · narration : voix de synthèse",
           "where": "Ouvrez-la dans l’outil à partir des liens « Où » de la fiche."},
}

CSS = """
html,body{margin:0;height:100%;background:#0b1626;color:#e8eef7;font-family:'IBM Plex Sans',system-ui,sans-serif}
.card{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;padding:0 9%;
  background:radial-gradient(1200px 700px at 85% 15%,#173a63 0,#0b1626 60%)}
.k{font:600 22px/1 'IBM Plex Mono',monospace;letter-spacing:.14em;color:#ffb000;text-transform:uppercase}
h1{font-weight:600;font-size:64px;line-height:1.08;margin:22px 0 18px;max-width:22ch}
p{font-size:28px;line-height:1.4;color:#b9c7da;max-width:46ch;margin:0}
ul{margin:26px 0 0;padding:0;list-style:none}
li{font-size:30px;line-height:1.35;margin:10px 0;padding-left:34px;position:relative}
li:before{content:'';position:absolute;left:0;top:.5em;width:14px;height:14px;border-radius:3px;background:#ffb000}
li code{font:500 24px 'IBM Plex Mono',monospace;color:#ffd27a;margin-right:12px}
.foot{position:absolute;left:9%;right:9%;bottom:48px;font-size:18px;color:#7f93ad;display:flex;justify-content:space-between}
"""


def _page(body: str, w: int, h: int) -> str:
    return (f"<!doctype html><html><head><meta charset=utf-8><link rel=stylesheet href='{DS.as_uri()}'>"
            f"<style>{CSS}</style></head><body style='width:{w}px;height:{h}px'>{body}</body></html>")


def title_html(sb: Storyboard, lang: str) -> str:
    l = L[lang]
    wk = l["week"].format(n=sb.week) + " · " if sb.week else ""
    return (f"<div class=card><div class=k>{html.escape(wk + sb.id)}</div>"
            f"<h1>{html.escape(tr(sb.title, lang))}</h1><p>{html.escape(tr(sb.summary, lang))}</p>"
            f"<div class=foot><span>{l['course']}</span><span>{l['licence']}</span></div></div>")


def end_html(sb: Storyboard, lang: str, ties: list[tuple[str, str]]) -> str:
    l = L[lang]
    items = "".join(f"<li><code>{html.escape(i)}</code>{html.escape(t)}</li>" for i, t in ties) or ""
    return (f"<div class=card><div class=k>{html.escape(sb.id)}</div><h1>{l['next']}</h1>"
            f"<ul>{items}</ul><p style='margin-top:28px'>{l['where']}</p>"
            f"<div class=foot><span>{l['course']}</span><span>{l['licence']}</span></div></div>")


async def _render(pages: list[tuple[str, Path]], w: int, h: int, scale: float) -> None:
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": w, "height": h}, device_scale_factor=scale)
        for body, out in pages:
            tmp = out.with_suffix(".html")
            tmp.write_text(_page(body, w, h), encoding="utf-8")
            await pg.goto(tmp.as_uri())
            await pg.wait_for_timeout(400)
            await pg.screenshot(path=str(out), type="jpeg", quality=95)
            tmp.unlink()
        await b.close()


def render(sb: Storyboard, lang: str, out_dir: Path, ties: list[tuple[str, str]]) -> tuple[Path, Path]:
    w, h = sb.viewport
    a, b = out_dir / "card_title.jpg", out_dir / "card_end.jpg"
    asyncio.run(_render([(title_html(sb, lang), a), (end_html(sb, lang, ties), b)], w, h, sb.scale))
    return a, b
