"""Command line: ``python -m c2ovideo <command>`` (run from ``video/``).

    fetch-models               download the Kokoro voice model (once, ~120 MB)
    fetch-h5p                  download the H5P runtime libraries (once, ~4 MB)
    list                       storyboards, weeks, ties
    validate [ID ...]          schema, worksheet ties, UI strings resolvable in FR
    narrate ID [--lang en,fr]  synthesise narration only (prints timings)
    build ID [--lang en,fr]    narrate → capture → assemble → H5P → review
         [--tts silence]       dry run without the voice model
         [--url app=http://…]  where the tools run (default: see capture.DEFAULT_URLS)
         [--publish]           and copy into the welcome page's video folder
    publish ID [--dir DIR]     copy a built video into SMO_VIDEO_DIR
    check ID [--lang ..]       speech-recognition check of the narration (optional)
    reviews                    print reviewers' notes saved on the welcome page
    stack setup sim|spacecdf   create sim/.venv or design/.venv (once, needs Python 3.11+)
    stack up|down spacecdf|sim|viz  run the tools on capture ports
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from . import LANGS, acronyms, assemble, h5p, review, storyboard, tts, uitext, worksheets
from .storyboard import ROOT, tr

OUT = Path(os.environ.get("C2O_VIDEO_OUT", ROOT / "out"))


def _langs(s: str | None) -> list[str]:
    ls = [x.strip() for x in (s or ",".join(LANGS)).split(",") if x.strip()]
    for l in ls:
        if l not in LANGS:
            raise SystemExit(f"unknown language {l}")
    return ls


def _urls(pairs: list[str] | None) -> dict:
    out = {}
    for k, v in os.environ.items():
        if k.startswith("C2O_VIDEO_URL_"):
            out[k[len("C2O_VIDEO_URL_"):].lower()] = v
    for p in pairs or []:
        k, _, v = p.partition("=")
        out[k] = v
    return out


def narrate(sb, lang: str, backend: str | None = None) -> dict[str, list[tts.Clip]]:
    return {st.id: tts.say(tr(st.say, lang), lang, backend) for st in sb.steps}


def _ui_strings(obj, app: str, found: list):
    if isinstance(obj, dict):
        a = obj.get("app", app)
        for key in ("name", "label", "text", "placeholder", "has_text"):
            v = obj.get(key)
            if isinstance(v, str) and ("role" in obj or key != "text" or "target" not in obj):
                found.append((a, v))
        for k, v in obj.items():
            if k in ("api", "python", "js", "storage"):
                continue                      # data for the server, not on-screen text
            if k == "goto" and isinstance(v, dict):
                a = v.get("app", a)
            _ui_strings(v, a, found)
    elif isinstance(obj, list):
        for v in obj:
            _ui_strings(v, app, found)


def validate(sb) -> list[str]:
    problems = []
    for t in (sb.ties.get("worksheets") or []) + (sb.ties.get("decisions") or []):
        try:
            worksheets.resolve(t)
        except KeyError as e:
            problems.append(str(e))
    for st in sb.steps:
        if st.question and st.question.get("worksheet"):
            try:
                worksheets.resolve(st.question["worksheet"])
            except KeyError as e:
                problems.append(f"{st.id}: {e}")
    found: list = []
    app0 = next(iter(sb.apps), "spacecdf")
    _ui_strings([{"do": s.do} for s in sb.steps] + sb.setup, app0, found)
    for app, s in found:
        if app in uitext.CATALOGS and "${" not in s:
            try:
                uitext.ui(app, s, "fr")
            except KeyError as e:
                problems.append(f"FR: {e}")
    return sorted(set(problems))


def _need_running(sb, overrides: dict) -> None:
    """Stop early, with the fix, when a tool the storyboard films is not running."""
    import urllib.request
    from . import capture
    urls = dict(capture.DEFAULT_URLS, **overrides)
    which = {"spacecdf": "spacecdf", "viz": "viz"}
    for app in sb.apps:
        url = urls.get(app)
        if not url:
            continue
        try:
            urllib.request.urlopen(url, timeout=5)
        except Exception:
            stack_name = which.get(app, "sim")
            raise SystemExit(f"{app} is not running at {url}.\n"
                             f"Start it first:  python -m c2ovideo stack up {stack_name}")


def cmd_build(a) -> int:
    from . import capture
    sb = storyboard.load(a.id)
    probs = validate(sb)
    if probs and not a.force:
        print("\n".join(f"  ✗ {p}" for p in probs))
        print("fix the storyboard (or --force)")
        return 2
    media = OUT / sb.slug
    media.mkdir(parents=True, exist_ok=True)
    all_clips: dict = {}
    for lang in _langs(a.lang):
        t = time.time()
        clips = narrate(sb, lang, a.tts)
        all_clips[lang] = clips
        secs = {k: tts.total_seconds(v) for k, v in clips.items()}
        print(f"[{lang}] narration {sum(secs.values()):.1f} s in {time.time() - t:.0f} s")
        take = media / f"take-{lang}"
        if not a.reuse_capture or not (take / "cues.json").exists():
            fresh = sb.raw.get("fresh_stack")
            if fresh:
                # every take starts from a just-started stack: same alarms,
                # same command history, same sim clock, in both languages
                from . import stack
                stack.run("down", fresh)
                if stack.run("up", fresh) != 0:
                    raise SystemExit(f"the {fresh} stack did not come up (see out/_stack/*.log)")
            _need_running(sb, _urls(a.url))
            t = time.time()
            res = capture.capture(sb, lang, secs, take, _urls(a.url), headful=a.headful)
            print(f"[{lang}] capture {res['cues'][-1]['end']:.1f} s, {len(res['frames'])} frames in {time.time() - t:.0f} s")
            for w in res["warnings"][:15]:
                print(f"   ! {w}")
        meta = assemble.build(sb, lang, take, clips, media)
        print(f"[{lang}] video {meta['duration']:.1f} s, {len(meta['chapters'])} chapters, {len(meta['questions'])} questions")
        for w in meta["warnings"]:
            if w.startswith("narration"):
                print(f"   ! {w}")
        info = h5p.build(sb, lang, media, meta)
        bad = {k: v for k, v in info["libraries"].items() if v not in ("MIT", "pd", None, "unspecified")}
        print(f"[{lang}] {info['package']}" + (f"  (non-MIT libraries: {bad})" if bad else ""))
    review.build(sb, all_clips, media)
    if a.publish:
        from . import publish
        print("published →", publish.publish(sb, media))
    print("done:", media)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="c2ovideo", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fetch-models")
    sub.add_parser("fetch-h5p")
    sub.add_parser("list")
    v = sub.add_parser("validate"); v.add_argument("ids", nargs="*")
    n = sub.add_parser("narrate"); n.add_argument("id"); n.add_argument("--lang"); n.add_argument("--tts")
    b = sub.add_parser("build")
    b.add_argument("id"); b.add_argument("--lang"); b.add_argument("--tts"); b.add_argument("--url", action="append")
    b.add_argument("--publish", action="store_true"); b.add_argument("--headful", action="store_true")
    b.add_argument("--reuse-capture", action="store_true", help="re-assemble from the last capture (narration unchanged)")
    b.add_argument("--force", action="store_true")
    p = sub.add_parser("publish"); p.add_argument("id"); p.add_argument("--dir")
    c = sub.add_parser("check"); c.add_argument("id"); c.add_argument("--lang"); c.add_argument("--model", default="small")
    sub.add_parser("reviews")
    s = sub.add_parser("stack"); s.add_argument("action", choices=["setup", "up", "down", "status"]); s.add_argument("which", nargs="?", default="spacecdf")
    a = ap.parse_args(argv)

    if a.cmd == "fetch-models":
        print(tts.fetch_models())
    elif a.cmd == "fetch-h5p":
        print(h5p.fetch_libraries(force=True))
    elif a.cmd == "list":
        for sb in storyboard.all_storyboards():
            ties = ", ".join((sb.ties.get("worksheets") or []) + (sb.ties.get("decisions") or []))
            print(f"{sb.id:14} wk{sb.week or '-':>2}  {tr(sb.title, 'en')}  [{ties}]")
    elif a.cmd == "validate":
        sbs = [storyboard.load(i) for i in a.ids] if a.ids else storyboard.all_storyboards()
        bad = 0
        for sb in sbs:
            probs = validate(sb)
            print(f"{sb.id}: {'ok' if not probs else str(len(probs)) + ' problem(s)'}")
            for pr in probs:
                print("   ✗", pr)
            for w in acronyms.lint(sb):
                print("   ! acronym:", w)
            bad += len(probs)
        return 1 if bad else 0
    elif a.cmd == "narrate":
        sb = storyboard.load(a.id)
        for lang in _langs(a.lang):
            clips = narrate(sb, lang, a.tts)
            for st in sb.steps:
                cs = clips[st.id]
                print(f"[{lang}] {st.id:14} {tts.total_seconds(cs):5.1f} s  {len(cs)} sentence(s)")
            print(f"[{lang}] total {sum(tts.total_seconds(c) for c in clips.values()):.1f} s")
    elif a.cmd == "build":
        return cmd_build(a)
    elif a.cmd == "publish":
        from . import publish
        sb = storyboard.load(a.id)
        print(publish.publish(sb, OUT / sb.slug, Path(a.dir) if a.dir else None))
    elif a.cmd == "check":
        from . import check
        return check.run(storyboard.load(a.id), _langs(a.lang), a.model)
    elif a.cmd == "reviews":
        from . import publish
        d = publish.video_dir() / "_review"
        for f in sorted(d.glob("*.json")) if d.exists() else []:
            notes = json.loads(f.read_text(encoding="utf-8"))
            for n in notes.get("notes", []):
                if n.get("status", "open") == "open":
                    print(f"{f.stem} {n.get('step')} [{n.get('lang')}] {n.get('by', '?')}: {n.get('text')}")
    elif a.cmd == "stack":
        from . import stack
        return stack.run(a.action, a.which)
    return 0


if __name__ == "__main__":
    sys.exit(main())
