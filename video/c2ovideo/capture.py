"""Screen capture of a real C2O tool, paced to the narration.

Frames come from the Chrome DevTools screencast (JPEG, only when the screen
changes, each with its own timestamp), not from Playwright's built-in video,
whose fixed low bitrate blurs small UI text. ``assemble`` turns the timestamped
frames into constant-frame-rate video.

Every step writes a cue (start, narration start, end) to ``cues.json``; captions,
chapters, H5P interaction times and the narration track are all placed from it.
"""

from __future__ import annotations

import asyncio
import base64
import importlib.util
import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .storyboard import REPO, Storyboard, tr
from .uitext import ui

OVERLAY = (Path(__file__).parent / "overlay.js").read_text(encoding="utf-8")
DEFAULT_URLS = {
    "spacecdf": "http://127.0.0.1:18800",
    "mcs": "http://127.0.0.1:9090",
    "planner": "http://127.0.0.1:9091",
    "instructor": "http://127.0.0.1:8080",
    "tools": "http://127.0.0.1:8093",
    "docs": "http://127.0.0.1:8094",
    "portal": "http://127.0.0.1:8090",
    "viz": "http://127.0.0.1:18801",
    "file": "",
}
MOVE_MS = 650


class CaptureError(RuntimeError):
    pass


@dataclass
class Ctx:
    sb: Storyboard
    lang: str
    urls: dict
    vars: dict = field(default_factory=dict)
    app: str = ""
    warnings: list = field(default_factory=list)

    def sub(self, v: Any) -> Any:
        if isinstance(v, str):
            return re.sub(r"\$\{(\w+)\}", lambda m: str(self.vars.get(m.group(1), m.group(0))), v)
        if isinstance(v, list):
            return [self.sub(x) for x in v]
        if isinstance(v, dict):
            if set(v) <= {"en", "fr"} and v:
                return self.sub(tr(v, self.lang))
            return {k: self.sub(x) for k, x in v.items()}
        return v


class Client:
    """Minimal requests-like client so repo seed helpers run against a live server."""

    class Resp:
        def __init__(self, status: int, body: bytes):
            self.status_code = status
            self.content = body
            self.text = body.decode("utf-8", "replace")

        def json(self):
            return json.loads(self.text) if self.text else None

        def raise_for_status(self):
            if self.status_code >= 400:
                raise CaptureError(f"HTTP {self.status_code}: {self.text[:300]}")

    def __init__(self, base: str, headers: dict | None = None):
        self.base = base.rstrip("/")
        self.headers = headers or {}

    def request(self, method: str, path: str, json_body: Any = None, params: dict | None = None, **_):
        url = self.base + path
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
        data = None if json_body is None else json.dumps(json_body).encode()
        h = {"Content-Type": "application/json", **self.headers}
        req = urllib.request.Request(url, data=data, method=method.upper(), headers=h)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return Client.Resp(r.status, r.read())
        except urllib.error.HTTPError as e:
            return Client.Resp(e.code, e.read())

    def get(self, path, **kw):
        return self.request("GET", path, params=kw.get("params"))

    def post(self, path, json=None, **kw):  # noqa: A002 - requests-compatible signature
        return self.request("POST", path, json, kw.get("params"))

    def put(self, path, json=None, **kw):  # noqa: A002
        return self.request("PUT", path, json, kw.get("params"))

    def patch(self, path, json=None, **kw):  # noqa: A002
        return self.request("PATCH", path, json, kw.get("params"))

    def delete(self, path, **kw):
        return self.request("DELETE", path, None, kw.get("params"))


import urllib.parse  # noqa: E402  (used by Client.request)


def _dig(obj: Any, dotted: str) -> Any:
    for part in dotted.split("."):
        if isinstance(obj, list):
            obj = obj[int(part)]
        else:
            obj = obj[part]
    return obj


def _load_callable(spec: str):
    file, _, fn = spec.partition(":")
    path = (REPO / file).resolve()
    mod_spec = importlib.util.spec_from_file_location(f"c2ovideo_ext_{path.stem}", path)
    mod = importlib.util.module_from_spec(mod_spec)
    mod_spec.loader.exec_module(mod)
    return getattr(mod, fn)


def locator(page, spec: Any, c: Ctx):
    if isinstance(spec, str):
        return page.locator(c.sub(spec)).first
    app = spec.get("app", c.app)
    base = page.locator(c.sub(spec["within"])).first if spec.get("within") else page
    exact = spec.get("exact", False)
    if "role" in spec:
        if "name" in spec:
            name = ui(app, c.sub(spec["name"]) if isinstance(spec["name"], str) else spec["name"], c.lang)
            loc = base.get_by_role(spec["role"], name=name, exact=exact)
        else:
            loc = base.get_by_role(spec["role"])
    elif "label" in spec:
        loc = base.get_by_label(ui(app, spec["label"], c.lang), exact=exact)
    elif "text" in spec:
        loc = base.get_by_text(ui(app, spec["text"], c.lang), exact=exact)
    elif "placeholder" in spec:
        loc = base.get_by_placeholder(ui(app, spec["placeholder"], c.lang), exact=exact)
    elif "css" in spec:
        loc = base.locator(c.sub(spec["css"]))
    else:
        raise CaptureError(f"locator needs role/label/text/placeholder/css: {spec}")
    if "has_text" in spec:
        loc = loc.filter(has_text=ui(app, spec["has_text"], c.lang))
    return loc.nth(int(spec.get("nth", 0)))


async def _point_at(page, loc, ms: int = MOVE_MS) -> None:
    await loc.scroll_into_view_if_needed(timeout=15000)
    box = await loc.bounding_box()
    if not box:
        return
    x = box["x"] + min(box["width"] / 2, 60 if box["width"] > 160 else box["width"] / 2)
    y = box["y"] + box["height"] / 2
    await page.evaluate("([x,y,ms]) => window.__c2oCursor && window.__c2oCursor.move(x,y,ms)", [x, y, ms])
    await page.wait_for_timeout(ms + 60)


async def _ring(page, loc, secs: float) -> None:
    await loc.scroll_into_view_if_needed(timeout=15000)
    box = await loc.bounding_box()
    if box:
        await page.evaluate("([l,t,w,h,s]) => window.__c2oCursor && window.__c2oCursor.ring(l,t,w,h,s)",
                            [box["x"], box["y"], box["width"], box["height"], secs])


async def run_action(page, act: dict, c: Ctx) -> None:
    if not isinstance(act, dict) or len(act) < 1:
        raise CaptureError(f"bad action {act!r}")
    kind = next(iter(act))
    arg = act[kind]
    if kind == "goto":
        a = arg if isinstance(arg, dict) else {"path": arg}
        c.app = a.get("app", c.app or next(iter(c.sb.apps), "spacecdf"))
        url = c.urls[c.app].rstrip("/") + c.sub(a.get("path", "/"))
        url = url.replace("{lang}", c.lang)
        await page.goto(url, wait_until=a.get("until", "load"))
        await page.wait_for_timeout(int(a.get("settle", 1.2) * 1000))
    elif kind in ("click", "dblclick", "check", "uncheck", "hover"):
        a = arg if isinstance(arg, dict) and ("target" in arg) else {"target": arg}
        loc = locator(page, a["target"], c)
        await loc.wait_for(state="visible", timeout=int(a.get("timeout", 20) * 1000))
        if not a.get("instant"):
            await _point_at(page, loc)
        if kind != "hover":
            await page.evaluate("() => window.__c2oCursor && window.__c2oCursor.click()")
        if kind == "click":
            await loc.click(timeout=15000)
        elif kind == "dblclick":
            await loc.dblclick(timeout=15000)
        elif kind == "check":
            await loc.check(timeout=15000)
        elif kind == "uncheck":
            await loc.uncheck(timeout=15000)
        await page.wait_for_timeout(int(a.get("settle", 0.5) * 1000))
    elif kind in ("fill", "type"):
        loc = locator(page, arg["target"], c)
        await loc.wait_for(state="visible", timeout=20000)
        await _point_at(page, loc)
        text = c.sub(arg["text"])
        if kind == "type" or arg.get("typed"):
            await loc.click()
            await loc.fill("")
            await loc.press_sequentially(text, delay=int(arg.get("delay_ms", 28)))
        else:
            await loc.fill(text)
        if arg.get("press"):
            await loc.press(arg["press"])
        await page.wait_for_timeout(int(arg.get("settle", 0.4) * 1000))
    elif kind == "press":
        a = arg if isinstance(arg, dict) else {"key": arg}
        if a.get("target"):
            await locator(page, a["target"], c).press(a["key"])
        else:
            await page.keyboard.press(a["key"])
        await page.wait_for_timeout(int(a.get("settle", 0.4) * 1000))
    elif kind == "select":
        loc = locator(page, arg["target"], c)
        await _point_at(page, loc)
        await loc.select_option(c.sub(arg["value"]))
        await page.wait_for_timeout(int(arg.get("settle", 0.6) * 1000))
    elif kind == "highlight":
        a = arg if isinstance(arg, dict) and "target" in arg else {"target": arg}
        loc = locator(page, a["target"], c)
        await loc.wait_for(state="visible", timeout=20000)
        if a.get("point", True):
            await _point_at(page, loc, 500)
        await _ring(page, loc, float(a.get("seconds", 2.6)))
    elif kind == "scroll":
        a = arg if isinstance(arg, dict) and "target" in arg else {"target": arg}
        await locator(page, a["target"], c).scroll_into_view_if_needed(timeout=15000)
        await page.wait_for_timeout(500)
    elif kind == "wait":
        await page.wait_for_timeout(int(float(arg) * 1000))
    elif kind == "wait_for":
        a = arg if isinstance(arg, dict) and "target" in arg else {"target": arg}
        await locator(page, a["target"], c).wait_for(state=a.get("state", "visible"), timeout=int(a.get("timeout", 30) * 1000))
    elif kind == "js":
        await page.evaluate(c.sub(arg))
    elif kind == "hash":
        await page.evaluate("(h) => { location.hash = h; }", c.sub(arg))
        await page.wait_for_timeout(900)
    elif kind == "reload":
        await page.reload(wait_until="load")
        await page.wait_for_timeout(int(float(arg or 1.5) * 1000))
    elif kind == "cursor":
        await page.evaluate(f"() => window.__c2oCursor && window.__c2oCursor.{'hide' if arg == 'hide' else 'show'}()")
    elif kind == "move":
        loc = locator(page, arg, c)
        await _point_at(page, loc)
    elif kind == "api":
        cl = Client(c.urls[arg.get("app", c.app)], arg.get("headers"))
        r = cl.request(arg.get("method", "GET"), c.sub(arg["path"]), c.sub(arg.get("json")))
        if r.status_code >= 400 and not arg.get("allow_error"):
            raise CaptureError(f"api {arg['path']}: HTTP {r.status_code} {r.text[:300]}")
        for var, dotted in (arg.get("save") or {}).items():
            c.vars[var] = _dig(r.json(), dotted)
    elif kind == "python":
        fn = _load_callable(arg["call"])
        cl = Client(c.urls[arg.get("app", c.app)])
        args = [cl if a == "client" else c.sub(a) for a in arg.get("args", ["client"])]
        res = fn(*args, **c.sub(arg.get("kwargs") or {}))
        if arg.get("save"):
            c.vars[arg["save"]] = res
    elif kind == "shot":
        await page.screenshot(path=str(c.vars["_take"] / f"shot_{arg}.png"))
    elif kind == "storage":
        await page.evaluate("([k,v]) => { try { localStorage.setItem(k, v); } catch (e) {} }", [arg["key"], c.sub(arg["value"])])
    else:
        raise CaptureError(f"unknown action {kind!r}")


async def _capture(sb: Storyboard, lang: str, narration: dict, out: Path, urls: dict, headful: bool) -> dict:
    from playwright.async_api import async_playwright

    out.mkdir(parents=True, exist_ok=True)
    frames_dir = out / "frames"
    if frames_dir.exists():
        for f in frames_dir.glob("*.jpg"):
            f.unlink()
    frames_dir.mkdir(exist_ok=True)
    frames: list = []
    c = Ctx(sb=sb, lang=lang, urls=urls, vars={"lang": lang, "_take": out}, app=next(iter(sb.apps), "spacecdf"))
    for app, base in urls.items():
        c.vars[f"{app}_url"] = base
    w, h = sb.viewport
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not headful, args=[
            "--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist", "--hide-scrollbars",
            "--force-color-profile=srgb", "--font-render-hinting=none",
            # the screencast honours this flag, not the context's device_scale_factor
            f"--force-device-scale-factor={sb.scale}"])
        ctx = await browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=sb.scale,
                                        locale="fr-FR" if lang == "fr" else "en-CA",
                                        timezone_id="UTC", accept_downloads=True,
                                        color_scheme=sb.raw.get("color_scheme", "light"))
        await ctx.add_init_script(OVERLAY)
        await ctx.add_init_script(f"try{{localStorage.setItem('scdf.lang','{lang}');localStorage.setItem('c2o.lang','{lang}');}}catch(e){{}}")
        page = await ctx.new_page()
        page.on("dialog", lambda d: asyncio.ensure_future(d.accept()))
        page.on("console", lambda m: c.warnings.append(f"console {m.type}: {m.text}")
                if m.type == "error" or "missingKey" in m.text else None)
        page.on("pageerror", lambda e: c.warnings.append(f"pageerror: {e}"))
        cdp = await ctx.new_cdp_session(page)

        def on_frame(ev):
            n = len(frames)
            f = frames_dir / f"{n:06d}.jpg"
            f.write_bytes(base64.b64decode(ev["data"]))
            frames.append((ev["metadata"]["timestamp"], f.name))
            asyncio.ensure_future(cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]}))

        cdp.on("Page.screencastFrame", on_frame)
        for act in sb.setup:
            await run_action(page, act, c)
        await cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92, "maxWidth": sb.size[0], "maxHeight": sb.size[1], "everyNthFrame": 1})
        await page.wait_for_timeout(400)
        # nudge a repaint so the first frame exists at t0
        await page.evaluate("() => { const d = document.createElement('div'); d.style.cssText='position:fixed;width:1px;height:1px;left:0;top:0;opacity:.01'; document.body.appendChild(d); setTimeout(() => d.remove(), 50); }")
        await page.wait_for_timeout(200)
        cues = []
        for st in sb.steps:
            t_start = time.time()
            say_s = float(narration.get(st.id, 0.0))
            say_at = None if st.say_after else t_start
            try:
                for act in st.do:
                    await run_action(page, act, c)
            except Exception as e:  # keep the evidence, then fail the take
                await page.screenshot(path=str(out / f"FAILED_{st.id}.png"))
                raise CaptureError(f"{sb.id} [{lang}] step {st.id}: {e}") from e
            if say_at is None:
                await page.wait_for_timeout(250)
                say_at = time.time()
            remaining = say_at + say_s + st.hold - time.time()
            if remaining > 0:
                await page.wait_for_timeout(int(remaining * 1000))
            cues.append({"id": st.id, "start": t_start, "say": say_at, "end": time.time()})
        await page.wait_for_timeout(600)
        await cdp.send("Page.stopScreencast")
        if lang == "fr":
            try:
                miss = await page.evaluate("() => (window.SMO_I18N && SMO_I18N.missing) ? Array.from(SMO_I18N.missing) : []")
                if miss:
                    c.warnings.append(f"untranslated UI strings on screen: {miss[:20]}")
            except Exception:
                pass
        await browser.close()
    t0 = cues[0]["start"]
    result = {
        "storyboard": sb.id, "lang": lang, "viewport": [w, h], "t0": t0,
        "cues": [{"id": q["id"], "start": round(q["start"] - t0, 3), "say": round(q["say"] - t0, 3),
                  "end": round(q["end"] - t0, 3)} for q in cues],
        "frames": [[round(ts - t0, 4), name] for ts, name in frames],
        "warnings": c.warnings[:200],
        "vars": {k: v for k, v in c.vars.items() if isinstance(v, (str, int, float))},
    }
    (out / "cues.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    return result


def capture(sb: Storyboard, lang: str, narration: dict, out: Path, urls: dict | None = None, headful: bool = False) -> dict:
    u = dict(DEFAULT_URLS)
    u.update(urls or {})
    u.update({k: v for k, v in (sb.apps or {}).items() if isinstance(v, str) and v.startswith("http") and k not in (urls or {})})
    return asyncio.run(_capture(sb, lang, narration, out, u, headful))
