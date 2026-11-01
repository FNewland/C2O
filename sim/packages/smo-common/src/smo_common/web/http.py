"""HTTP delivery policy shared by every SMO aiohttp server (R3 audit A8).

The suite's servers (simulator/instructor, MCS, planner, the ``sim/tools``
pages) used to send every asset uncompressed and either uncached or
``no-cache``. On a LAN that is invisible; over ``c2o.live`` a console reload
cost 1-2 MB. This module gives all of them one policy:

**Compression** -- :func:`compression_middleware` gzips text responses
(HTML, CSS, JS, JSON, SVG, XML, plain text) of at least ``min_size`` bytes
(default 1 KB) when the client accepts gzip. It handles both ``web.Response``
bodies and static ``web.FileResponse`` files. It leaves alone anything already
prepared (WebSockets, streamed downloads), anything that already has a
``Content-Encoding``, range requests, and binary types (PNG, fonts, ZIP).

**Caching** -- :func:`cache_middleware` decides ``Cache-Control`` for static
files:

* a URL carrying ``?v=<hash>`` where ``<hash>`` equals :func:`asset_hash` of
  the file actually served gets ``public, max-age=31536000, immutable``;
* any other ``?v=`` (for example a hand-written ``?v=1``) is *not* trusted:
  the 2026-08-20 field defect was exactly a hard-coded ``?v=1`` that Chrome
  cached heuristically, so a stale module ran against a fresh page. Such
  URLs fall through to the rules below;
* paths under ``max_age_prefixes`` (third-party vendor bundles) get
  ``public, max-age=<n>``;
* paths under ``revalidate_prefixes`` (the app's own assets) get
  ``no-cache`` -- "revalidate before use", which with aiohttp's ETag costs a
  bodiless 304 when nothing changed.

A ``Cache-Control`` header the handler set itself is never overwritten.

**Versioned URLs** -- :func:`stamp_asset_versions` rewrites the
``src``/``href`` attributes of an HTML page that point at ``/static/...``
so they carry the real content hash (``?v=3f9a01c2be``). Call it on the HTML
a page handler is about to send; the matching files then become immutable in
the browser and change URL whenever their content changes. ES-module
``import`` statements inside JS are not rewritten; those files stay on the
``no-cache`` + ETag rule, which is correct, just not free.

Typical wiring (a server that mounts its own ``/static/``)::

    from smo_common.web.http import apply_http_policy, stamp_asset_versions

    app = web.Application()
    apply_http_policy(app, max_age_prefixes={"/static/vendor/": 86400})
    ...
    html = stamp_asset_versions(page.read_text(encoding="utf-8"), app)
    return web.Response(text=html, content_type="text/html")

The tool servers in ``sim/tools`` additionally use :func:`mount_shared_ui` to
serve the shared design system and ``i18n.js`` at ``/static/shared/``, and
:func:`relative_display_path` so a web-hosted page never prints an absolute
server path.
"""

from __future__ import annotations

import hashlib
import logging
import mimetypes
import os
import re
from pathlib import Path
from typing import Iterable, Mapping

from aiohttp import hdrs, web
from aiohttp.web_urldispatcher import StaticResource

logger = logging.getLogger(__name__)

__all__ = [
    "IMMUTABLE",
    "apply_http_policy",
    "asset_hash",
    "cache_middleware",
    "compression_middleware",
    "mount_shared_ui",
    "relative_display_path",
    "shared_ui_dir",
    "setup_tool_app",
    "stamp_asset_versions",
    "tool_html_response",
    "TOOL_HEAD",
]

#: Cache-Control for a content-hashed asset URL.
IMMUTABLE = "public, max-age=31536000, immutable"

_COMPRESSIBLE_PREFIXES = ("text/",)
_COMPRESSIBLE_TYPES = frozenset({
    "application/javascript", "application/x-javascript", "text/javascript",
    "application/json", "application/manifest+json", "application/ld+json",
    "application/xml", "application/xhtml+xml", "image/svg+xml",
    "application/x-ndjson", "application/geo+json",
})


def _compressible(content_type: str | None) -> bool:
    if not content_type:
        return False
    ct = content_type.split(";", 1)[0].strip().lower()
    return ct.startswith(_COMPRESSIBLE_PREFIXES) or ct in _COMPRESSIBLE_TYPES


# ── content hashes ─────────────────────────────────────────────────────

_HASH_CACHE: dict[str, tuple[int, int, str]] = {}


def asset_hash(path: str | os.PathLike) -> str | None:
    """Short (10 hex) SHA-256 of a file's content, or None if unreadable.

    Cached per path and invalidated by mtime/size, so calling it on every
    request costs one ``stat``.
    """
    p = str(path)
    try:
        st = os.stat(p)
    except OSError:
        return None
    hit = _HASH_CACHE.get(p)
    if hit and hit[0] == st.st_mtime_ns and hit[1] == st.st_size:
        return hit[2]
    h = hashlib.sha256()
    try:
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    except OSError:
        return None
    digest = h.hexdigest()[:10]
    _HASH_CACHE[p] = (st.st_mtime_ns, st.st_size, digest)
    return digest


def _static_mounts(app: web.Application) -> list[tuple[str, Path]]:
    """(url prefix ending in '/', directory) for every add_static mount, in
    registration order -- the order aiohttp resolves them in."""
    out = []
    for res in app.router.resources():
        if isinstance(res, StaticResource):
            prefix = res.canonical.rstrip("/") + "/"
            directory = getattr(res, "_directory", None)
            if directory is not None:
                out.append((prefix, Path(directory)))
    return out


def _resolve_static(mounts: list[tuple[str, Path]], url_path: str) -> Path | None:
    for prefix, directory in mounts:
        if url_path.startswith(prefix):
            rel = url_path[len(prefix):]
            cand = (directory / rel).resolve()
            try:
                cand.relative_to(directory.resolve())
            except ValueError:
                return None
            return cand if cand.is_file() else None
    return None


_ASSET_ATTR = re.compile(
    r"""(?P<lead>\b(?:src|href)\s*=\s*["'])"""
    r"""(?P<path>/static/[^"'?#\s]+\.(?:js|mjs|css|svg|png|jpg|jpeg|webp|woff2?|json))"""
    r"""(?P<query>\?[^"'#]*)?"""
    r"""(?P<tail>["'])""",
    re.IGNORECASE,
)


def stamp_asset_versions(html: str, app: web.Application) -> str:
    """Rewrite ``/static/...`` src/href URLs in *html* to ``?v=<content hash>``.

    Only URLs that resolve to a file under one of *app*'s static mounts are
    touched; any other query parameters on the URL are kept. Unresolvable
    URLs are left exactly as written.
    """
    mounts = _static_mounts(app)
    if not mounts:
        return html

    def repl(m: re.Match) -> str:
        f = _resolve_static(mounts, m.group("path"))
        digest = asset_hash(f) if f else None
        if not digest:
            return m.group(0)
        q = m.group("query") or ""
        params = [kv for kv in q.lstrip("?").split("&")
                  if kv and not kv.startswith("v=")]
        params.append("v=" + digest)
        return f'{m.group("lead")}{m.group("path")}?{"&".join(params)}{m.group("tail")}'

    return _ASSET_ATTR.sub(repl, html)


# ── middlewares ────────────────────────────────────────────────────────

def _file_path(resp: web.StreamResponse) -> Path | None:
    # FileResponse keeps the path it will send in `_path` (aiohttp 3.x).
    p = getattr(resp, "_path", None)
    return Path(p) if p is not None else None


def _would_be_not_modified(request: web.Request, st: os.stat_result) -> bool:
    """Mirror FileResponse's conditional logic: True if it will answer 304
    (or 412) instead of sending the file."""
    etag = f"{st.st_mtime_ns:x}-{st.st_size:x}"
    inm = request.headers.get(hdrs.IF_NONE_MATCH)
    if inm is not None:
        tags = {t.strip().removeprefix("W/").strip('"') for t in inm.split(",")}
        return "*" in tags or etag in tags
    ims = request.if_modified_since
    if ims is not None and st.st_mtime <= ims.timestamp():
        return True
    return request.if_unmodified_since is not None or hdrs.IF_MATCH in request.headers


def compression_middleware(min_size: int = 1024):
    """Middleware factory: gzip compressible responses of >= *min_size* bytes."""

    @web.middleware
    async def _gzip(request: web.Request, handler):
        resp = await handler(request)
        try:
            if (not isinstance(resp, web.StreamResponse) or resp.prepared
                    or isinstance(resp, web.WebSocketResponse)
                    or hdrs.CONTENT_ENCODING in resp.headers
                    or resp.status < 200 or resp.status in (204, 304)):
                return resp
            # 1. Is this response a compression candidate at all?
            st = None
            if isinstance(resp, web.FileResponse):
                fp = _file_path(resp)
                if fp is None:
                    return resp
                ctype = resp.headers.get(hdrs.CONTENT_TYPE) or mimetypes.guess_type(fp.name)[0]
                try:
                    st = fp.stat()
                except OSError:
                    return resp            # FileResponse will answer 404 itself
                size = st.st_size
            elif isinstance(resp, web.Response):
                body = resp.body
                if not isinstance(body, (bytes, bytearray)):
                    return resp
                ctype, size = resp.content_type, len(body)
            else:
                return resp
            if size < min_size or not _compressible(ctype):
                return resp
            # 2. Its representation depends on Accept-Encoding: say so, so a
            #    shared cache never hands gzip to a client that cannot take it.
            vary = resp.headers.get(hdrs.VARY, "")
            if "accept-encoding" not in vary.lower():
                resp.headers[hdrs.VARY] = (vary + ", " if vary else "") + "Accept-Encoding"
            # 3. Compress when the client accepts it and a body will be sent.
            if ("gzip" not in request.headers.get(hdrs.ACCEPT_ENCODING, "").lower()
                    or request.method == "HEAD" or hdrs.RANGE in request.headers):
                return resp
            if st is not None and _would_be_not_modified(request, st):
                # aiohttp would write a gzip trailer into the bodiless 304
                # and corrupt the connection; a 304 has no body anyway.
                return resp
            resp.enable_compression(web.ContentCoding.gzip)
        except Exception:  # noqa: BLE001 -- compression must never break a page
            logger.debug("compression skipped for %s", request.path, exc_info=True)
        return resp

    return _gzip


def cache_middleware(revalidate_prefixes: Iterable[str] = ("/static/",),
                     max_age_prefixes: Mapping[str, int] | None = None):
    """Middleware factory: ``Cache-Control`` for static assets (see module doc)."""
    reval = tuple(revalidate_prefixes)
    max_age = dict(max_age_prefixes or {})

    @web.middleware
    async def _cache(request: web.Request, handler):
        resp = await handler(request)
        if (not isinstance(resp, web.StreamResponse) or resp.prepared
                or hdrs.CACHE_CONTROL in resp.headers):
            return resp
        p = request.path
        v = request.query.get("v")
        if v and isinstance(resp, web.FileResponse):
            fp = _file_path(resp)
            if fp is not None and asset_hash(fp) == v:
                resp.headers[hdrs.CACHE_CONTROL] = IMMUTABLE
                return resp
        for prefix, secs in max_age.items():
            if p.startswith(prefix):
                resp.headers[hdrs.CACHE_CONTROL] = f"public, max-age={int(secs)}"
                return resp
        if any(p.startswith(x) for x in reval):
            resp.headers[hdrs.CACHE_CONTROL] = "no-cache"
        return resp

    return _cache


def apply_http_policy(app: web.Application, *,
                      revalidate_prefixes: Iterable[str] = ("/static/",),
                      max_age_prefixes: Mapping[str, int] | None = None,
                      min_size: int = 1024) -> web.Application:
    """Append the cache and gzip middlewares to *app* (before it starts)."""
    app.middlewares.append(cache_middleware(revalidate_prefixes, max_age_prefixes))
    app.middlewares.append(compression_middleware(min_size))
    return app


# ── shared UI + display paths ──────────────────────────────────────────

def shared_ui_dir() -> Path:
    """The shared design-system directory (``smo_common/ui``)."""
    return Path(__file__).resolve().parent.parent / "ui"


def mount_shared_ui(app: web.Application, prefix: str = "/static/shared/") -> bool:
    """Serve ``smo_common/ui`` (design-system.css, i18n.js, catalogs) at
    *prefix*. Returns False, with a warning, if the package data is missing."""
    d = shared_ui_dir()
    if not d.is_dir():
        logger.warning("smo_common ui/ package data missing (%s)", d)
        return False
    app.router.add_static(prefix, d)
    return True


def relative_display_path(path: str | os.PathLike | None,
                          base: str | os.PathLike | None = None) -> str:
    """A path safe to show on a web page: relative to *base* (default: the
    current working directory) when inside it, otherwise just the last two
    components (``…/dumps``). Never the absolute server path."""
    if path is None or str(path) == "":
        return ""
    p = Path(path)
    if not p.is_absolute():
        return p.as_posix()
    try:
        rel = p.resolve().relative_to(Path(base or os.getcwd()).resolve())
        return rel.as_posix() or "."
    except (ValueError, OSError):
        tail = p.parts[-2:] if len(p.parts) > 2 else p.parts[1:]
        return "…/" + "/".join(tail) if tail else p.name


# ── stand-alone tool pages (sim/tools) ─────────────────────────────────

#: <head> markup that gives a tool page the shared design-system tokens and
#: the suite language runtime (tool-page.js). Put it BEFORE the page's own
#: <style> so page rules (written against the DS tokens) win on conflicts.
TOOL_HEAD = (
    '<link rel="stylesheet" href="/static/shared/design-system.css">\n'
    '<script type="module" src="/static/shared/tool-page.js"></script>\n'
)


def setup_tool_app(app: web.Application) -> web.Application:
    """One call for a ``sim/tools`` server: gzip + cache policy, and the
    shared UI mounted at ``/static/shared/``."""
    apply_http_policy(app, revalidate_prefixes=("/static/",),
                      max_age_prefixes={"/vendor/": 86400})
    mount_shared_ui(app)
    return app


def tool_html_response(html: str, app: web.Application, **kw) -> web.Response:
    """A tool page response: asset URLs content-stamped, ``no-cache``."""
    headers = kw.pop("headers", None) or {}
    headers.setdefault(hdrs.CACHE_CONTROL, "no-cache")
    return web.Response(text=stamp_asset_versions(html, app),
                        content_type="text/html", headers=headers, **kw)
