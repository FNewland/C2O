#!/usr/bin/env python3
"""wall.py — the planner's wall display, public and read-only (wall.c2o.live).

The planner's /wide page is a non-interactive wall screen (no buttons, no forms). Classroom
screens and VR headsets should be able to show it without signing in, while the planner,
mission control and everything else stay behind sign-in. This small server is the only thing
behind wall.<domain>, which the load balancer serves with no sign-in. It is a filter, not a
general proxy:

  * GET and HEAD only; any other method gets 405.
  * An exact allowlist: the page itself, the static files it loads (its scripts, the shared
    design system, fonts and translation catalogues), and the nine planner data feeds it
    polls. Everything else gets 404, including every planner route that changes anything.
  * Two feeds come from other services and are cut down to what the page reads: the MCS
    state is reduced to its ``derived`` block, the radio's pass summaries to ``rollups`` and
    ``active``. The planner configuration is reduced to the planner's own display settings,
    with the MCS and radio addresses pointed at this server (/mcs, /rf).
  * Query strings are rebuilt, never passed through: only ``lang`` on the page, ``v`` on
    static files, and bounded numbers on the ground-track feed survive.
  * Nothing from the visitor's request is forwarded upstream (no cookies, no headers).
  * Every answer is cached for a few seconds and shared by all viewers, and concurrent
    viewers share one upstream fetch, so a room of headsets costs the planner one request
    per feed per few seconds. Upstream answers are size- and time-limited.

Run: python tools/wall.py --port 8099   (defaults: planner 127.0.0.1:9091, MCS :9090, radio :8094)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from typing import Optional

try:
    import aiohttp
    from aiohttp import web
except ImportError:                       # pragma: no cover - environment
    print("ERROR: aiohttp required. Install: pip install aiohttp")
    raise SystemExit(1)

logger = logging.getLogger("wall")

DEFAULT_PORT = 8099
MAX_BYTES = 6 * 1024 * 1024          # largest upstream answer accepted (fonts, ground track)
UPSTREAM_TIMEOUT_S = 6.0
UPSTREAM_PARALLEL = 8                 # upstream fetches in flight at once

#: Planner JSON feeds the page polls: path -> seconds an answer is shared.
PLANNER_FEEDS = {
    "/api/budget/data": 5.0,
    "/api/budget/power": 5.0,
    "/api/contacts": 5.0,
    "/api/ground-stations": 300.0,
    "/api/schedule": 5.0,
    "/api/spacecraft-state": 2.0,
    "/api/time-source": 5.0,
}
#: Static files the page loads, by pattern (no "..": each segment is a plain name).
STATIC_PATTERNS = (
    re.compile(r"/static/modern/(wide|wide-basemap)\.js"),
    re.compile(r"/static/modern/i18n/[a-z]{2}\.json"),
    re.compile(r"/static/shared/(format|i18n|state)\.js"),
    re.compile(r"/static/shared/design-system\.css"),
    re.compile(r"/static/shared/fonts/[A-Za-z0-9-]+\.woff2"),
    re.compile(r"/static/shared/i18n/[a-z]{2}(\.db)?\.json"),
)
STATIC_TTL_S = 300.0
PAGE_TTL_S = 60.0
CONTENT_TYPES = {
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".woff2": "font/woff2",
}
#: The page's browser policy: its own files only, no forms, no plugins; it may be framed
#: (a headset app or a room-screen dashboard can embed it).
CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
       "img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; "
       "base-uri 'none'; form-action 'none'; frame-ancestors *")
LANG_RE = re.compile(r"[a-z]{2}")
VERSION_RE = re.compile(r"[A-Za-z0-9._-]{1,16}")


@dataclass
class Upstreams:
    planner: str = "http://127.0.0.1:9091"
    mcs: Optional[str] = "http://127.0.0.1:9090"
    radio: Optional[str] = "http://127.0.0.1:8094"


@dataclass
class _Entry:
    at: float
    status: int
    body: bytes
    ctype: str


class Wall:
    def __init__(self, up: Upstreams, clock=time.monotonic):
        self.up = up
        self._clock = clock
        self._cache: dict[str, _Entry] = {}
        self._inflight: dict[str, asyncio.Future] = {}
        self._sem = asyncio.Semaphore(UPSTREAM_PARALLEL)
        self._session: Optional[aiohttp.ClientSession] = None

    # -- upstream, cached and shared ------------------------------------------

    async def _session_get(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=UPSTREAM_TIMEOUT_S),
                cookie_jar=aiohttp.DummyCookieJar())
        return self._session

    async def _fetch(self, url: str) -> tuple[int, bytes, str]:
        async with self._sem:
            s = await self._session_get()
            async with s.get(url, allow_redirects=False) as r:
                body = await r.content.read(MAX_BYTES + 1)
                if len(body) > MAX_BYTES:
                    raise ValueError("upstream answer too large")
                return r.status, body, r.headers.get("Content-Type", "")

    async def cached(self, key: str, url: str, ttl: float, transform=None) -> _Entry:
        """One upstream fetch per key per ``ttl`` seconds, shared by every viewer; viewers
        arriving while it is in flight wait for the same answer. ``transform`` turns the
        upstream JSON into what the page may see."""
        now = self._clock()
        e = self._cache.get(key)
        if e is not None and now - e.at < ttl:
            return e
        fut = self._inflight.get(key)
        if fut is not None:
            return await asyncio.shield(fut)
        fut = asyncio.get_running_loop().create_future()
        self._inflight[key] = fut
        try:
            try:
                status, body, ctype = await self._fetch(url)
                if status == 200 and transform is not None:
                    body = json.dumps(transform(json.loads(body)), separators=(",", ":")).encode()
                    ctype = "application/json; charset=utf-8"
                entry = _Entry(now, status if status == 200 else 502, body if status == 200 else b"", ctype)
            except Exception as ex:  # noqa: BLE001 - unreachable, slow, too big, bad JSON
                logger.info("upstream %s: %s", key, type(ex).__name__)
                entry = _Entry(now, 502, b"", "")
            if entry.status == 200:
                self._cache[key] = entry
            elif e is not None and e.status == 200 and now - e.at < 4 * ttl:
                entry = e                    # keep serving the last good answer briefly
            else:                            # a failure is retried after 2 s, not after ttl
                self._cache[key] = _Entry(now - ttl + min(2.0, ttl), 502, b"", "")
                entry = self._cache[key]
            fut.set_result(entry)
            return entry
        except BaseException as ex:          # pragma: no cover - cancellation
            if not fut.done():
                fut.set_exception(ex)
            raise
        finally:
            self._inflight.pop(key, None)

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()

    # -- what the page may see --------------------------------------------------

    def planner_config(self, d: dict) -> dict:
        """The planner's display settings, with the MCS and radio addresses on this server
        (only those this server relays; an absent one is the page's designed "no data")."""
        cfg = dict((d or {}).get("planner_config") or {})
        cfg["services"] = {"mcs_url": "/mcs" if self.up.mcs else None,
                           "rfsim_url": "/rf" if self.up.radio else None}
        return {"planner_config": cfg}

    @staticmethod
    def mcs_state(d: dict) -> dict:
        return {"derived": (d or {}).get("derived")}

    @staticmethod
    def rollups(d: dict) -> dict:
        d = d or {}
        return {"rollups": list(d.get("rollups") or [])[-5:], "active": d.get("active")}

    # -- request handling ---------------------------------------------------------

    def _reply(self, e: _Entry, *, ttl: float, cors: bool = False, ctype: str = "") -> web.Response:
        if e.status != 200:
            return web.json_response({"error": "not available right now"}, status=502,
                                     headers=self._headers(0, cors))
        return web.Response(body=e.body, status=200,
                            headers=dict(self._headers(ttl, cors),
                                         **{"Content-Type": ctype or e.ctype or "application/octet-stream"}))

    @staticmethod
    def _headers(ttl: float, cors: bool) -> dict:
        h = {"Cache-Control": f"public, max-age={int(ttl)}" if ttl else "no-store",
             "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer",
             "Content-Security-Policy": CSP}
        if cors:
            h["Access-Control-Allow-Origin"] = "*"
        return h

    async def handle(self, request: web.Request) -> web.StreamResponse:
        if request.method not in ("GET", "HEAD"):
            return web.Response(status=405, headers={"Allow": "GET, HEAD"})
        path = request.path
        if "//" in path or ".." in path or len(path) > 128:
            raise web.HTTPNotFound()
        q = request.query

        if path == "/healthz":
            return web.json_response({"ok": True})
        if path in ("/", "/wide"):
            lang = q.get("lang", "")
            lang = lang if LANG_RE.fullmatch(lang) else ""
            url = f"{self.up.planner}/wide?ui=modern" + (f"&lang={lang}" if lang else "")
            e = await self.cached("page:" + lang, url, PAGE_TTL_S)
            return self._reply(e, ttl=PAGE_TTL_S, ctype="text/html; charset=utf-8")
        if any(p.fullmatch(path) for p in STATIC_PATTERNS):
            v = q.get("v", "")
            ext = os.path.splitext(path)[1]
            url = f"{self.up.planner}{path}" + (f"?v={v}" if VERSION_RE.fullmatch(v) else "")
            e = await self.cached("static:" + path, url, STATIC_TTL_S)
            return self._reply(e, ttl=STATIC_TTL_S, cors=True, ctype=CONTENT_TYPES.get(ext, ""))
        if path in PLANNER_FEEDS:
            ttl = PLANNER_FEEDS[path]
            return self._reply(await self.cached(path, self.up.planner + path, ttl), ttl=ttl, cors=True)
        if path == "/api/config/planner":
            e = await self.cached(path, self.up.planner + path, 60.0, self.planner_config)
            return self._reply(e, ttl=60.0, cors=True)
        if path == "/api/ground-track":
            # The page asks for its timeline span at 120 s steps: whole hours 1-48, step fixed,
            # so no visitor can make the planner compute a long fine-grained track.
            hours = int(round(_bounded(q.get("duration_hours"), 1.0, 48.0, 24.0)))
            qs = f"duration_hours={hours}&step_s=120"
            e = await self.cached("track:" + qs, f"{self.up.planner}{path}?{qs}", 30.0)
            return self._reply(e, ttl=30.0, cors=True)
        if path == "/mcs/api/state" and self.up.mcs:
            e = await self.cached(path, self.up.mcs + "/api/state", 5.0, self.mcs_state)
            return self._reply(e, ttl=5.0, cors=True)
        if path == "/rf/api/pass-rollups" and self.up.radio:
            e = await self.cached(path, self.up.radio + "/api/pass-rollups?limit=5", 10.0, self.rollups)
            return self._reply(e, ttl=10.0, cors=True)
        raise web.HTTPNotFound()


def _bounded(raw, lo: float, hi: float, default: float) -> float:
    try:
        v = float(raw)
    except (TypeError, ValueError):
        return default
    if v != v:                                  # NaN
        return default
    return max(lo, min(hi, v))


def build_app(up: Upstreams, clock=time.monotonic) -> web.Application:
    wall = Wall(up, clock)
    app = web.Application(client_max_size=1024)          # no request bodies wanted
    app.router.add_route("*", "/{tail:.*}", wall.handle)

    async def _close(_app):
        await wall.close()
    app.on_cleanup.append(_close)
    app["wall"] = wall
    return app


def main(argv=None) -> int:
    e = os.environ.get
    ap = argparse.ArgumentParser(description="The planner's wall display, public and read-only.")
    ap.add_argument("--host", default=e("SMO_WALL_BIND", "0.0.0.0"))
    ap.add_argument("--port", type=int, default=int(e("SMO_WALL_PORT", str(DEFAULT_PORT))))
    ap.add_argument("--planner", default=e("SMO_WALL_PLANNER_URL", "http://127.0.0.1:9091"))
    ap.add_argument("--mcs", default=e("SMO_WALL_MCS_URL", "http://127.0.0.1:9090"),
                    help="MCS base for the derived readouts; 'off' to leave them out")
    ap.add_argument("--radio", default=e("SMO_WALL_RADIO_URL", "http://127.0.0.1:8094"),
                    help="radio (rfsim) base for pass summaries; 'off' to leave them out")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s wall %(levelname)s %(message)s")
    up = Upstreams(planner=args.planner.rstrip("/"),
                   mcs=None if args.mcs == "off" else args.mcs.rstrip("/"),
                   radio=None if args.radio == "off" else args.radio.rstrip("/"))
    logger.info("wall display on %s:%d (planner %s)", args.host, args.port, up.planner)
    web.run_app(build_app(up), host=args.host, port=args.port, access_log=None, print=None)
    return 0


if __name__ == "__main__":
    sys.exit(main())
