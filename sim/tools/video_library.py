"""Course videos on the welcome page: library, interactive player, narration review.

The videos are made by ``video/`` (python -m c2ovideo build ... --publish) and
copied into ``SMO_VIDEO_DIR`` (default ``workspace/videos``); see
``video/c2ovideo/publish.py`` for the folder layout. This module only serves
what is there:

* ``/videos``                  the library, by week, in the page language
* ``/videos/<slug>``           the H5P Interactive Video (h5p-standalone); every
                               answer to an embedded question goes into the
                               viewer's logbook, against the worksheet it serves
* ``/videos/<slug>/review``    narration review, EN and FR side by side, with a
                               note per step (instructors and SMO_VIDEO_REVIEWERS)
* ``/media/videos/...``        the files (MP4, captions, posters, H5P packages)

Videos and their text are CC0 1.0; the H5P runtime is MIT (vendor/js/h5p-standalone).
"""

from __future__ import annotations

import html
import json
import os
import re
import threading
from datetime import datetime, timezone
from pathlib import Path

from aiohttp import web

REPO = Path(__file__).resolve().parents[1]
VENDOR_H5P = REPO / "vendor" / "js" / "h5p-standalone"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,40}$")
_lock = threading.Lock()


def T(s: str) -> str:
    """Marks an English UI string for the tools catalogue (translated in the browser)."""
    return s


def video_dir() -> Path:
    return Path(os.environ.get("SMO_VIDEO_DIR", REPO / "workspace" / "videos"))


def review_dir() -> Path:
    return Path(os.environ.get("SMO_VIDEO_REVIEW_DIR", REPO / "workspace" / "video-review"))


def reviewers() -> set[str]:
    # comma or space separated (vm-bootstrap.sh writes the space form)
    return {x.lower() for x in re.split(r"[,;\s]+", os.environ.get("SMO_VIDEO_REVIEWERS", "")) if x}


def catalog() -> dict:
    f = video_dir() / "catalog.json"
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"videos": []}


def visible(cat: dict, instructor: bool) -> list[dict]:
    return [v for v in cat.get("videos", []) if instructor or v.get("audience", "all") != "instructors"]


PAGE_CSS = """
.vl-main{max-width:1180px;margin:0 auto;padding:24px 20px 64px}
.vl-intro{color:var(--ink-2);max-width:72ch;margin:4px 0 22px}
.vl-week{margin:26px 0 8px;font-size:var(--fs-sm,13px);letter-spacing:.08em;text-transform:uppercase;color:var(--ink-3)}
.vl-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}
.vl-card{background:var(--surface-1);border:1px solid var(--line-1);border-radius:10px;overflow:hidden;display:flex;flex-direction:column}
.vl-card img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block;background:var(--surface-2)}
.vl-body{padding:12px 14px 14px;display:flex;flex-direction:column;gap:8px;flex:1}
.vl-body h3{margin:0;font-size:1.05rem;line-height:1.3}
.vl-body p{margin:0;color:var(--ink-2);font-size:.92rem}
.vl-meta{color:var(--ink-3);font-size:.85rem}
.vl-ties{display:flex;flex-wrap:wrap;gap:6px}
.vl-ties .ds-chip{font-family:var(--mono,monospace);font-size:.78rem}
.vl-acts{display:flex;flex-wrap:wrap;gap:8px;margin-top:auto;padding-top:6px}
.vl-empty{padding:28px;border:1px dashed var(--line-2);border-radius:10px;color:var(--ink-2)}
.vp-main{max-width:1180px;margin:0 auto;padding:18px 20px 64px;display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:22px}
@media (max-width:960px){.vp-main{grid-template-columns:1fr}}
.vp-side section{background:var(--surface-1);border:1px solid var(--line-1);border-radius:10px;padding:12px 14px;margin-bottom:14px}
.vp-side h2{font-size:.95rem;margin:0 0 8px}
.vp-side ol,.vp-side ul{margin:0;padding-left:18px}
.vp-side li{margin:4px 0}
.vp-side button.linkish{display:inline;background:none;border:0;padding:0;color:var(--accent,#2d6cdf);cursor:pointer;text-align:left;font:inherit}
.vp-note{font-size:.85rem;color:var(--ink-3)}
#h5p-box{background:#000;border-radius:10px;overflow:hidden;min-height:200px}
.vr-main{max-width:1320px;margin:0 auto;padding:18px 20px 64px}
.vr-step{border:1px solid var(--line-1);border-radius:10px;margin:14px 0;background:var(--surface-1)}
.vr-step>header{padding:10px 14px;border-bottom:1px solid var(--line-1);font-weight:600}
.vr-cols{display:grid;grid-template-columns:1fr 1fr;gap:0}
@media (max-width:900px){.vr-cols{grid-template-columns:1fr}}
.vr-col{padding:12px 14px}
.vr-col+.vr-col{border-left:1px solid var(--line-1)}
.vr-sent{display:flex;gap:8px;align-items:flex-start;margin:6px 0}
.vr-sent button{flex:none}
.vr-spoken{color:var(--ink-3);font-size:.82rem}
.vr-warn{color:var(--caution,#b26a00);font-size:.85rem}
.vr-col textarea{width:100%;min-height:54px;margin-top:8px}
.vr-notes{font-size:.85rem;color:var(--ink-2);margin-top:6px}
"""


def _boot(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def _shell(title_html: str, body: str, boot: dict, js: str, *, lang: str, extra_head: str = "") -> str:
    import tool_frame
    bar = tool_frame.bar(title_html, meta_html='<a href="/" data-i18n>Welcome page</a>', logbook="portal")
    return f"""<!DOCTYPE html>
<html lang="{html.escape(lang)}"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>C2O</title>
{tool_frame.head(extra_css=PAGE_CSS)}
{extra_head}
</head><body>
<a class="ds-skip" href="#content" data-i18n>Skip to content</a>
{bar}
{body}
<script id="vl-boot" type="application/json">{_boot(boot)}</script>
{tool_frame.SCRIPT}
{js}
</body></html>"""


LIBRARY_JS = """<script type="module">
import { esc } from "/static/shared/components.js";
import I18n from "/static/shared/i18n.js";
const T = (s, v) => I18n.tText(s, v);
const B = JSON.parse(document.getElementById("vl-boot").textContent);
const tr = (o) => (o && (o[I18n.getLang()] || o.en)) || "";
const mmss = (s) => `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, "0")}`;
function card(v) {
  const L = I18n.getLang();
  const d = (v.langs || {})[L] || (v.langs || {}).en;
  if (!d) return "";
  const base = `/media/videos/${v.slug}/`;
  const ties = (v.ties || []).map((t) => `<span class="ds-chip" title="${esc(tr(t.label))}">${esc(t.id)}</span>`).join("");
  let acts = `<a class="ds-btn is-primary" href="/videos/${v.slug}?lang=${L}">${esc(T("Watch"))}</a>`
    + `<a class="ds-btn" href="${base}${esc(d.transcript)}" download>${esc(T("Transcript"))}</a>`;
  if (B.instructor) {
    for (const l of ["en", "fr"]) if ((v.langs || {})[l]) acts += `<a class="ds-btn" href="${base}${esc(v.langs[l].h5p)}" download>${esc(T("H5P for Brightspace ({{lang}})", { lang: l.toUpperCase() }))}</a>`;
  }
  if (B.reviewer) acts += `<a class="ds-btn" href="/videos/${v.slug}/review?lang=${L}">${esc(T("Review narration"))}</a>`;
  const q = d.questions ? T("{{n}} questions", { n: d.questions }) : "";
  return `<article class="vl-card"><img src="${base}${esc(d.poster)}" alt="" loading="lazy">
    <div class="vl-body"><h3>${esc(tr(v.title))}</h3><p>${esc(tr(v.summary))}</p>
    <div class="vl-meta">${esc(mmss(d.duration))}${q ? " · " + esc(q) : ""} · ${esc(v.id)}</div>
    ${ties ? `<div class="vl-ties" aria-label="${esc(T("Workbook parts this video prepares"))}">${ties}</div>` : ""}
    <div class="vl-acts">${acts}</div></div></article>`;
}
function paint() {
  const box = document.getElementById("vl-list");
  const vids = B.videos || [];
  if (!vids.length) { box.innerHTML = `<p class="vl-empty">${esc(T("No videos have been published yet."))}</p>`; return; }
  const weeks = new Map();
  for (const v of vids) { const k = v.week || 0; if (!weeks.has(k)) weeks.set(k, []); weeks.get(k).push(v); }
  box.innerHTML = [...weeks.entries()].sort((a, b) => a[0] - b[0]).map(([w, vs]) =>
    `<h2 class="vl-week">${esc(w ? T("Week {{n}}", { n: w }) : T("Any week"))}</h2><div class="vl-grid">${vs.map(card).join("")}</div>`).join("");
}
paint();
I18n.onLangChange(paint);
</script>"""


PLAYER_JS = """<script src="/vendor/h5p/main.bundle.js"></script>
<script type="module">
import { esc } from "/static/shared/components.js";
import I18n from "/static/shared/i18n.js";
const T = (s, v) => I18n.tText(s, v);
const B = JSON.parse(document.getElementById("vl-boot").textContent);
const L = B.lang;
const tr = (o) => (o && (o[L] || o.en)) || "";
const status = document.getElementById("vp-status");
function say(msg) { if (status) status.textContent = msg; }

// Answers to embedded questions -> the viewer's logbook (private, 48 h).
const bySub = new Map((B.questions || []).map((q) => [q.subContentId, q]));
function answerText(st) {
  const r = (st.result || {}).response;
  const def = (st.object || {}).definition || {};
  if (r === undefined || r === null) return "";
  if (Array.isArray(def.choices) && def.choices.length) {
    return String(r).split("[,]").map((i) => {
      const c = def.choices.find((x) => String(x.id) === String(i));
      const d = c && c.description ? (c.description[L] || c.description["en-US"] || Object.values(c.description)[0]) : i;
      return String(d).replace(/<[^>]+>/g, "").trim();
    }).join("; ");
  }
  if (def.interactionType === "true-false") return r === "true" ? T("True") : T("False");
  return String(r).split("[,]").join("; ");
}
async function log(q, st) {
  const ans = answerText(st);
  if (!ans) return;
  const res = st.result || {};
  const ok = res.success === true ? T("correct") : res.success === false ? T("not correct") : "";
  const text = `${tr(B.title)} — ${q.text}\\n${T("Answer: {{a}}", { a: ans })}${ok ? " (" + ok + ")" : ""}`;
  const body = { kind: q.worksheet ? "worksheet" : "reflection", tool: "portal", lang: L, text,
    context: { video: B.slug, step: q.step } };
  if (q.worksheet) {
    const [id, part] = q.worksheet.split("/");
    body.worksheet = { id, q: part || "", q_text: q.text, title: q.worksheet_label || "" };
  }
  try {
    const r = await fetch("/api/logbook/entries", { method: "POST", credentials: "same-origin",
      headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    if (r.ok) {
      say(T("Saved in your logbook: {{q}}", { q: q.worksheet || q.step }));
      window.dispatchEvent(new CustomEvent("c2o:logbook-changed"));
    }
  } catch (e) { /* the video keeps playing; the logbook is best-effort */ }
}
const el = document.getElementById("h5p-box");
const opts = {
  h5pJsonPath: `/media/videos/${B.slug}/h5p/${L}`,
  librariesPath: "/media/videos/h5p-libraries",
  frameJs: "/vendor/h5p/frame.bundle.js",
  frameCss: "/vendor/h5p/styles/h5p.css",
  fullScreen: true, frame: false, copyright: false, export: false, embed: false,
  customCss: [],
};
function h5pWindows() {
  const wins = [window];
  el.querySelectorAll("iframe").forEach((f) => { try { if (f.contentWindow && f.contentWindow.H5P) wins.push(f.contentWindow); } catch (e) { /* cross-origin */ } });
  return wins;
}
function findVideo() {
  for (const w of h5pWindows()) { const v = w.document.querySelector("video"); if (v) return v; }
  return null;
}
const seen = new Set();
new H5PStandalone.H5P(el, opts).then(() => {
  for (const w of h5pWindows()) {
    if (!w.H5P || !w.H5P.externalDispatcher || seen.has(w)) continue;
    seen.add(w);
    w.H5P.externalDispatcher.on("xAPI", (ev) => {
    const st = ev.data && ev.data.statement;
    if (!st || !st.verb || !/answered$/.test(st.verb.id || "")) return;
    const ext = ((st.object || {}).definition || {}).extensions || {};
    const id = (st.object || {}).id || "";
    const sub = (id.match(/subContentId=([0-9a-f-]+)/) || [])[1] || ext["http://h5p.org/x-api/h5p-subContentId"];
    const q = bySub.get(sub);
    if (q) log(q, st);
    });
  }
}).catch(() => {
  el.innerHTML = `<video controls preload="metadata" style="width:100%" src="/media/videos/${B.slug}/${esc(B.mp4)}">
    <track kind="subtitles" srclang="${L}" src="/media/videos/${B.slug}/${esc(B.vtt)}" default></video>`;
});
document.querySelectorAll("[data-seek]").forEach((b) => b.addEventListener("click", () => {
  const v = findVideo();
  if (v) { v.currentTime = Number(b.dataset.seek); v.play(); }
}));
</script>"""


REVIEW_JS = """<script type="module">
import { esc } from "/static/shared/components.js";
import I18n from "/static/shared/i18n.js";
const T = (s, v) => I18n.tText(s, v);
const B = JSON.parse(document.getElementById("vl-boot").textContent);
const base = `/media/videos/${B.slug}/review/`;
let R = null, N = { notes: [] };
const audio = new Audio();
function col(step, lang) {
  const d = step[lang] || {};
  const sents = (d.sentences || []).map((s) =>
    `<div class="vr-sent"><button class="ds-btn is-sm" data-play="${esc(s.audio)}" aria-label="${esc(T("Play"))}">▶</button>
      <div><div>${esc(s.text)}</div>${s.spoken !== s.text ? `<div class="vr-spoken">${esc(T("Spoken as"))}: ${esc(s.spoken)}</div>` : ""}</div></div>`).join("");
  const unk = (d.unknown || []).length ? `<div class="vr-warn">${esc(T("Check the pronunciation of"))}: ${esc(d.unknown.join(", "))}</div>` : "";
  const q = d.question ? `<div class="vr-notes"><b>${esc(T("Question"))}:</b> ${esc(d.question.text)}${(d.question.options || []).length ? "<ul>" + d.question.options.map((o) => `<li>${esc(o)}</li>`).join("") + "</ul>" : ""}</div>` : "";
  const mine = N.notes.filter((n) => n.step === step.id && n.lang === lang)
    .map((n) => `<div class="vr-notes">• ${esc(n.by || "")}: ${esc(n.text)}</div>`).join("");
  return `<div class="vr-col" lang="${lang}"><div class="vl-meta">${lang.toUpperCase()} · ${esc(d.title || "")}</div>${sents}${unk}${q}${mine}
    <label class="ds-sr" for="n-${step.id}-${lang}">${esc(T("Note"))}</label>
    <textarea id="n-${step.id}-${lang}" placeholder="${esc(T("What should change? (wording, pronunciation, terminology)"))}"></textarea>
    <button class="ds-btn is-sm" data-save="${step.id}" data-lang="${lang}">${esc(T("Save note"))}</button></div>`;
}
function paint() {
  const box = document.getElementById("vr-list");
  if (!R) { box.textContent = T("Loading…"); return; }
  box.innerHTML = R.steps.map((s) => `<section class="vr-step"><header>${esc(s.id)}</header><div class="vr-cols">${col(s, "en")}${col(s, "fr")}</div></section>`).join("");
}
async function load() {
  try { R = await (await fetch(base + "review.json", { cache: "no-store" })).json(); } catch (e) { R = { steps: [] }; }
  try { N = await (await fetch(`/api/videos/${B.slug}/review`, { cache: "no-store", credentials: "same-origin" })).json(); } catch (e) { /* none yet */ }
  paint();
}
document.addEventListener("click", async (ev) => {
  const p = ev.target.closest("[data-play]");
  if (p) { audio.src = base + p.dataset.play; audio.play(); return; }
  const s = ev.target.closest("[data-save]");
  if (s) {
    const ta = document.getElementById(`n-${s.dataset.save}-${s.dataset.lang}`);
    const text = (ta.value || "").trim();
    if (!text) return;
    const r = await fetch(`/api/videos/${B.slug}/review`, { method: "POST", credentials: "same-origin",
      headers: { "Content-Type": "application/json" }, body: JSON.stringify({ step: s.dataset.save, lang: s.dataset.lang, text }) });
    if (r.ok) { N = await r.json(); paint(); }
  }
});
load();
I18n.onLangChange(paint);
</script>"""


def library_page(*, lang: str, instructor: bool, reviewer: bool) -> str:
    cat = catalog()
    body = ('<main id="content" class="vl-main">'
            '<h1 data-i18n>Course videos</h1>'
            '<p class="vl-intro" data-i18n>Short walkthroughs of the tools. Questions pause the video; your answers go into your logbook, against the worksheet they belong to.</p>'
            '<div id="vl-list"></div></main>')
    boot = {"videos": visible(cat, instructor), "instructor": instructor, "reviewer": reviewer}
    return _shell('<span data-i18n>Course videos</span>', body, boot, LIBRARY_JS, lang=lang)


def player_page(v: dict, *, lang: str) -> str | None:
    d = (v.get("langs") or {}).get(lang) or (v.get("langs") or {}).get("en")
    if not d:
        return None
    if lang not in (v.get("langs") or {}):
        lang = "en"
    e = html.escape
    title = (v.get("title") or {}).get(lang) or v["id"]
    chapters = "".join(f'<li><button class="linkish" data-seek="{c["start"]}">{e(c["title"])}</button></li>'
                       for c in d.get("chapter_list", []))
    ties = "".join(f'<li><code>{e(t["id"])}</code> {e((t.get("label") or {}).get(lang, ""))}</li>' for t in v.get("ties", []))
    base = f'/media/videos/{v["slug"]}/'
    body = (f'<main id="content" class="vp-main"><div><h1>{e(title)}</h1>'
            f'<div id="h5p-box" aria-label="{e(title)}"></div>'
            '<p class="vp-note" id="vp-status" role="status" aria-live="polite"></p></div>'
            '<aside class="vp-side">'
            f'<section><h2 data-i18n>Chapters</h2><ol>{chapters}</ol></section>'
            f'<section><h2 data-i18n>In your workbook</h2><ul>{ties}</ul>'
            '<p class="vp-note" data-i18n>Answers to the questions in the video are saved in your logbook. Download it at the end of the session.</p></section>'
            f'<section><h2 data-i18n>Downloads</h2><ul>'
            f'<li><a href="{base}{e(d["transcript"])}" download data-i18n>Transcript</a></li>'
            f'<li><a href="{base}{e(d["vtt"])}" download data-i18n>Captions (WebVTT)</a></li>'
            f'<li><a href="{base}{e(d["mp4"])}" download data-i18n>Video file (MP4)</a></li></ul>'
            '<p class="vp-note" data-i18n>Public domain (CC0 1.0): reuse freely.</p></section>'
            '<p><a href="/videos" data-i18n>All course videos</a></p></aside></main>')
    boot = {"slug": v["slug"], "lang": lang, "title": v.get("title"), "mp4": d["mp4"], "vtt": d["vtt"],
            "questions": d.get("question_list", [])}
    head = '<link rel="stylesheet" href="/vendor/h5p/styles/h5p.css">'
    return _shell('<span data-i18n>Course videos</span>', body, boot, PLAYER_JS, lang=lang, extra_head=head)


def review_page(v: dict, *, lang: str) -> str:
    e = html.escape
    links = " · ".join(f'<a href="/videos/{v["slug"]}?lang={l}">{l.upper()}</a>' for l in (v.get("langs") or {}))
    body = (f'<main id="content" class="vr-main"><h1><span data-i18n>Narration review</span>: {e(v["id"])}</h1>'
            '<p class="vl-intro" data-i18n>Listen to each sentence in both languages. Note anything that sounds wrong: a word, a pronunciation, a term that is not the one used in class. Notes are kept for the people who re-render the video.</p>'
            f'<p><span data-i18n>Watch the full video</span>: {links}</p><div id="vr-list"></div></main>')
    return _shell('<span data-i18n>Narration review</span>', body, {"slug": v["slug"]}, REVIEW_JS, lang=lang)


def _notes_file(slug: str) -> Path:
    return review_dir() / f"{slug}.json"


def read_notes(slug: str) -> dict:
    try:
        return json.loads(_notes_file(slug).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"notes": []}


def add_note(slug: str, step: str, lang: str, text: str, by: str) -> dict:
    with _lock:
        data = read_notes(slug)
        data["notes"].append({"step": step[:40], "lang": "fr" if lang == "fr" else "en", "text": text[:2000],
                              "by": by[:120], "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                              "status": "open"})
        data["notes"] = data["notes"][-500:]
        f = _notes_file(slug)
        f.parent.mkdir(parents=True, exist_ok=True)
        tmp = f.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
        tmp.replace(f)
        return data


def register(app: web.Application, *, is_instructor, user_of) -> None:
    """Add the video routes to the welcome page. ``is_instructor(request)`` and
    ``user_of(request)`` come from the portal (IAP identity)."""
    from smo_common.web.http import tool_html_response

    def _lang(request) -> str:
        return "fr" if (request.query.get("lang") or "").lower().startswith("fr") else "en"

    def _reviewer(request) -> bool:
        if is_instructor(request):
            return True
        u = (user_of(request) or "").lower()
        return bool(u) and u in reviewers()

    def _find(request) -> dict:
        slug = request.match_info["slug"]
        if not SLUG_RE.match(slug):
            raise web.HTTPNotFound()
        for v in visible(catalog(), is_instructor(request)):
            if v["slug"] == slug:
                return v
        raise web.HTTPNotFound()

    async def library(request):
        return tool_html_response(library_page(lang=_lang(request), instructor=is_instructor(request),
                                               reviewer=_reviewer(request)), app)

    async def player(request):
        page = player_page(_find(request), lang=_lang(request))
        if page is None:
            raise web.HTTPNotFound()
        return tool_html_response(page, app)

    async def review(request):
        if not _reviewer(request):
            raise web.HTTPForbidden(text="Narration review is for instructors and reviewers.")
        return tool_html_response(review_page(_find(request), lang=_lang(request)), app)

    async def notes_get(request):
        if not _reviewer(request):
            raise web.HTTPForbidden()
        return web.json_response(read_notes(_find(request)["slug"]), headers={"Cache-Control": "no-store"})

    async def notes_post(request):
        if not _reviewer(request):
            raise web.HTTPForbidden()
        v = _find(request)
        try:
            body = await request.json()
        except ValueError:
            raise web.HTTPBadRequest(text="JSON body expected")
        text = str(body.get("text") or "").strip()
        step = str(body.get("step") or "")
        if not text or not re.match(r"^[a-z0-9][a-z0-9_-]{0,40}$", step):
            raise web.HTTPBadRequest(text="step and text are required")
        return web.json_response(add_note(v["slug"], step, str(body.get("lang") or "en"), text,
                                          user_of(request) or "local"))

    app.router.add_get("/videos", library)
    app.router.add_get("/videos/{slug}", player)
    app.router.add_get("/videos/{slug}/review", review)
    app.router.add_get("/api/videos/{slug}/review", notes_get)
    app.router.add_post("/api/videos/{slug}/review", notes_post)
    d = video_dir()
    d.mkdir(parents=True, exist_ok=True)
    app.router.add_static("/media/videos", str(d), follow_symlinks=True, show_index=False)
    if VENDOR_H5P.exists():
        app.router.add_static("/vendor/h5p", str(VENDOR_H5P))
