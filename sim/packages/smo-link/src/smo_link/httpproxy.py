"""Proxied HTTP and nested WebSocket over link streams (LINK_DESIGN §3.7).

GSG side (:func:`gsg_proxy`): Host check, route **allowlist** on the fully
normalised path, Origin check, request-header allowlist; opens a stream with
``OPEN {kind, method, path, query, headers}`` (``path`` is the canonical,
re-encoded path that was checked), streams the request body as DATA (FIN on
the last chunk), then relays the agent's ``OPEN {status, headers}`` and body
with a response-header allowlist plus safe headers (nosniff, CSP, ...).

Agent side (:func:`agent_serve_stream`): enforces the same allowlist again on
the path it receives AND on the final upstream URL it builds (defence in
depth: it is the side next to the simulator), then performs the request
against the simulator's HTTP port with ``auto_decompress=False`` and no total
timeout, or opens a WebSocket to it and relays messages (one DATA per
message, FIN-terminated chunks, TEXT flag for text).
"""
from __future__ import annotations

import asyncio
import ipaddress
import logging
import re
from typing import Any, Iterable
from urllib.parse import quote, unquote, urlsplit

import aiohttp
from aiohttp import WSMsgType, web
from yarl import URL

from . import protocol as P
from .mux import Stream, StreamClosed

logger = logging.getLogger("smo_link.proxy")

MAX_REQUEST_BODY = 8 * 1024 * 1024
WS_MAX_MSG = 4 * 1024 * 1024
OPEN_TIMEOUT_S = 30.0

# --- route allowlist (M1) ---------------------------------------------------
#
# Derived from smo_simulator/instructor/app.py and the libraries it mounts
# (smo_common.dump_store, smo_common.reporting): the instructor console
# (classic + modern), its JSON API and command endpoints, static assets, the
# /ws socket (console and rfsim) and the READ-ONLY dump and report views.
# Not listed, hence unreachable: the config editor (/config, /api/config/*),
# POST /api/reports/{validate,generate} (reports are produced on the ground),
# /api/state (served locally by the GSG) and anything else.

_SEG = r"[A-Za-z0-9_~-][A-Za-z0-9._~-]*"       # no leading dot: no hidden files

READ_EXACT = frozenset({
    "/", "/classic", "/modern",
    "/api/instructor/snapshot", "/api/vr", "/api/scenarios", "/api/scenario/debrief",
    "/api/failures", "/api/failure-catalog", "/api/breakpoints",
    "/dumps", "/api/dumps", "/api/dumps/", "/api/dumps/file", "/api/dumps/summary",
    "/reports", "/api/reports", "/api/reports/", "/api/reports/templates",
    "/api/reports/file",
})
READ_PATTERNS = tuple(re.compile(p, re.ASCII) for p in (
    rf"/static/(?:{_SEG}/)*{_SEG}",
    rf"/api/dumps/{_SEG}",
    rf"/api/dumps/{_SEG}/summary",
    rf"/api/reports/templates/{_SEG}",
))
COMMAND_EXACT = frozenset({"/api/command", "/api/breakpoint/save", "/api/breakpoint/load"})
WS_EXACT = frozenset({"/ws"})

READ_METHODS = frozenset({"GET", "HEAD"})
_QUERY_RE = re.compile(r"[\x21-\x22\x24-\x7e]*", re.ASCII)   # printable ASCII, no '#', no space


def normalise_path(raw: str) -> str | None:
    """Canonical form of a request target's path, or None if it is malformed
    or escapes the root.

    Fragment and query are stripped; ``;params`` are stripped from every
    segment; the path is percent-decoded ONCE and refused if it still holds a
    ``%`` (double encoding), a backslash, NUL or any control/space/non-ASCII
    character; ``//`` collapses; ``.`` and ``..`` are resolved (escaping the
    root is refused). A trailing slash is kept. Matching is case-sensitive.
    """
    if not isinstance(raw, str):
        return None
    path = raw.split("#", 1)[0].split("?", 1)[0]
    if not path.startswith("/"):
        return None
    path = "/".join(seg.split(";", 1)[0] for seg in path.split("/"))
    try:
        path = unquote(path, errors="strict")
    except UnicodeDecodeError:
        return None
    if any(c in path for c in "%\\") or not path.isascii() \
            or any(ord(c) < 0x21 or ord(c) == 0x7F for c in path):
        return None
    out: list[str] = []
    for seg in path.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if not out:
                return None
            out.pop()
        else:
            out.append(seg)
    norm = "/" + "/".join(out)
    if path.endswith("/") and norm != "/":
        norm += "/"
    return norm


def route_allowed(method: str, norm: str, websocket: bool = False) -> bool:
    if websocket:
        return method == "GET" and norm in WS_EXACT
    if method in READ_METHODS:
        return norm in READ_EXACT or any(p.fullmatch(norm) for p in READ_PATTERNS)
    if method == "POST":
        return norm in COMMAND_EXACT
    return False


def check_route(method: str, raw_target: str, websocket: bool = False
                ) -> tuple[str | None, str | None]:
    """``(canonical encoded path, None)`` if allowed, else ``(None, reason)``."""
    norm = normalise_path(raw_target)
    if norm is None:
        return None, "malformed path or path escapes root"
    if not route_allowed(str(method), norm, websocket):
        return None, "route not on the space-link allowlist"
    return encode_path(norm), None


def encode_path(norm: str) -> str:
    return quote(norm, safe="/-._~!$&'()*+,=:@")


def deny_reason(method: str, raw_target: str, websocket: bool = False) -> str | None:
    """Why this request is not proxied (None = allowed)."""
    return check_route(method, raw_target, websocket)[1]


def split_query(raw_target: str) -> str:
    target = raw_target.split("#", 1)[0]
    return target.split("?", 1)[1] if "?" in target else ""


def query_ok(query: str) -> bool:
    return isinstance(query, str) and len(query) <= 8192 and bool(_QUERY_RE.fullmatch(query))


# --- headers (H3) -----------------------------------------------------------

#: Client -> simulator. Nothing else crosses: in particular never Cookie,
#: Authorization, X-Goog-IAP-*, Proxy-*, Forwarded / X-Forwarded-*.
REQUEST_HEADER_ALLOW = frozenset(h.lower() for h in (
    "Accept", "Accept-Encoding", "Accept-Language", "Content-Type",
    "If-None-Match", "If-Modified-Since", "If-Match", "If-Unmodified-Since", "If-Range",
    "Range", "Cache-Control", "Pragma", "User-Agent", "X-Requested-With",
))
#: Simulator -> browser. Never Set-Cookie, Location, Link, Refresh, CORS or
#: security-policy headers chosen by the space side.
RESPONSE_HEADER_ALLOW = frozenset(h.lower() for h in (
    "Content-Type", "Content-Length", "Content-Encoding", "Cache-Control", "ETag",
    "Last-Modified", "Content-Disposition", "Content-Range", "Accept-Ranges",
))
_HEADER_NAME_RE = re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]{1,64}", re.ASCII)
_HOST_RE = re.compile(r"[A-Za-z0-9.\-]+(?::[0-9]{1,5})?|\[[0-9A-Fa-f:.]+\](?::[0-9]{1,5})?",
                      re.ASCII)


def _header_items(headers: Iterable) -> list[tuple[str, str]]:
    out = []
    for item in headers or []:
        try:
            k, v = str(item[0]), str(item[1])
        except (IndexError, TypeError):
            continue
        if not _HEADER_NAME_RE.fullmatch(k) or any(c in v for c in "\r\n\x00") or len(v) > 8192:
            continue
        out.append((k, v))
    return out


def filter_request_headers(headers: Iterable) -> list[tuple[str, str]]:
    return [(k, v) for k, v in _header_items(headers) if k.lower() in REQUEST_HEADER_ALLOW]


def filter_response_headers(headers: Iterable) -> list[tuple[str, str]]:
    return [(k, v) for k, v in _header_items(headers) if k.lower() in RESPONSE_HEADER_ALLOW]


def content_security_policy(host: str | None) -> str:
    """Blocks third-party script, style, font, image, frame and connect
    sources and every cross-origin form/fetch/WebSocket. ``'unsafe-inline'``
    for script and style is needed by the classic console (inline handlers)."""
    connect = "'self'"
    if host and _HOST_RE.fullmatch(host):
        connect += f" ws://{host} wss://{host}"
    return ("default-src 'self'; script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
            "font-src 'self' data:; media-src 'self'; connect-src " + connect + "; "
            "worker-src 'none'; object-src 'none'; base-uri 'self'; "
            "form-action 'self'; frame-ancestors 'self'")


def safe_response_headers(host: str | None) -> list[tuple[str, str]]:
    return [("X-Content-Type-Options", "nosniff"),
            ("Content-Security-Policy", content_security_policy(host)),
            ("X-Frame-Options", "SAMEORIGIN"),
            ("Referrer-Policy", "same-origin"),
            ("Cross-Origin-Resource-Policy", "same-origin")]


def origin_allowed(origin: str | None, host: str | None, allowed: list[str]) -> bool:
    """No Origin (non-browser client) is allowed. Otherwise the Origin must be
    in ``allowed`` or, when that is empty, have the same host:port as Host."""
    if not origin:
        return True
    origin = origin.strip().rstrip("/")
    if allowed:
        return origin in {a.strip().rstrip("/") for a in allowed}
    if origin == "null":
        return False
    try:
        netloc = urlsplit(origin).netloc
    except ValueError:
        return False
    return bool(host) and netloc.lower() == host.strip().lower()


def _hostname(host: str) -> str:
    h = host.strip().lower()
    if h.startswith("["):
        return h[1:h.find("]")] if "]" in h else h
    return h.rsplit(":", 1)[0] if h.count(":") == 1 else h


def host_allowed(host: str | None, allowed_hosts: Iterable[str]) -> bool:
    """DNS-rebinding guard (L11): the Host must be an IP literal, ``localhost``
    or one of ``allowed_hosts`` (hostnames, port ignored). A rebinding attack
    needs an attacker-controlled *name*, so IP literals are safe."""
    if not host or not _HOST_RE.fullmatch(host.strip()):
        return False
    name = _hostname(host)
    if name in ("localhost", "localhost.localdomain"):
        return True
    try:
        ipaddress.ip_address(name)
        return True
    except ValueError:
        pass
    return name in {_hostname(h) for h in allowed_hosts if h}


def hosts_from_origins(origins: Iterable[str]) -> list[str]:
    out = []
    for o in origins:
        try:
            netloc = urlsplit(o.strip()).netloc
        except ValueError:
            continue
        if netloc:
            out.append(netloc)
    return out


# --- GSG side ---------------------------------------------------------------

def _forbidden(reason: str, host: str | None) -> web.Response:
    resp = web.json_response({"error": "forbidden", "reason": reason}, status=403)
    for k, v in safe_response_headers(host):
        resp.headers[k] = v
    return resp


async def gsg_proxy(request: web.Request, link: Any, allowed_origins: list[str],
                    allowed_hosts: Iterable[str] = ()) -> web.StreamResponse:
    host = request.headers.get("Host")
    if not host_allowed(host, list(allowed_hosts) + hosts_from_origins(allowed_origins)):
        logger.info(P.kv("proxy_host_denied", host=str(host)[:100]))
        return _forbidden("host not allowed", None)
    is_ws = (request.headers.get("Upgrade", "").lower() == "websocket"
             and request.method == "GET")
    raw_target = request.raw_path
    path, reason = check_route(request.method, raw_target, websocket=is_ws)
    if path is None:
        logger.info(P.kv("proxy_denied", method=request.method[:16],
                         path=raw_target[:200], reason=reason))
        return _forbidden(str(reason), host)
    query = split_query(raw_target)
    if not query_ok(query):
        return _forbidden("malformed query", host)
    if not origin_allowed(request.headers.get("Origin"), host, allowed_origins):
        logger.info(P.kv("proxy_origin_denied", path=path[:200]))
        return _forbidden("origin not allowed", host)
    if link is None or link.closed:
        return web.json_response({"error": "space link down"}, status=503,
                                 headers=dict(safe_response_headers(host)))
    headers = filter_request_headers(request.headers.items())
    if request.headers.get("Origin"):
        headers.append(("Origin", "checked"))     # the agent rewrites it to the sim's origin
    open_msg = {"kind": "ws" if is_ws else "http", "method": request.method,
                "path": path, "query": query, "headers": headers}
    if is_ws:
        protos = [p.strip() for p in request.headers.get("Sec-WebSocket-Protocol", "").split(",")
                  if p.strip() and _HEADER_NAME_RE.fullmatch(p.strip())]
        open_msg["protocols"] = protos[:8]
        return await _gsg_ws(request, link, open_msg)
    return await _gsg_http(request, link, open_msg)


def _status(head: dict, default: int = 502) -> int:
    try:
        st = int(head.get("status", default))
    except (TypeError, ValueError):
        return default
    return st if 100 <= st <= 599 else default


async def _gsg_http(request: web.Request, link: Any, open_msg: dict) -> web.StreamResponse:
    host = request.headers.get("Host")
    if request.content_length is not None and request.content_length > MAX_REQUEST_BODY:
        return web.json_response({"error": "request body too large"}, status=413)
    s = link.open_stream()
    resp: web.StreamResponse | None = None
    try:
        s.send_open(open_msg)
        sent = 0
        async for chunk in request.content.iter_chunked(P.CHUNK):
            sent += len(chunk)
            if sent > MAX_REQUEST_BODY:
                s.send_close(1009, "body too large")
                return web.json_response({"error": "request body too large"}, status=413)
            await s.send_data(chunk)
        await s.send_data(b"", fin=True)
        head = await asyncio.wait_for(s.open_msg, OPEN_TIMEOUT_S)
        resp = web.StreamResponse(status=_status(head))
        for k, v in filter_response_headers(head.get("headers", [])):
            resp.headers.add(k, v)
        for k, v in safe_response_headers(host):
            resp.headers[k] = v
        await resp.prepare(request)
        while True:
            item = await s.recv()
            if item is None:  # closed before FIN: truncated body
                raise StreamClosed(s.id)
            flags, payload = item
            if payload:
                await resp.write(payload)
            if flags & P.FIN:
                break
        await resp.write_eof()
        return resp
    except (StreamClosed, asyncio.TimeoutError, ConnectionError) as e:
        if resp is None:
            return web.json_response({"error": "space link stream failed",
                                      "detail": type(e).__name__}, status=502)
        # Headers already sent: abort the client connection mid-body.
        if request.transport is not None:
            request.transport.close()
        return resp
    finally:
        if not s.closed:
            s.send_close(0, "done")


async def _gsg_ws(request: web.Request, link: Any, open_msg: dict) -> web.StreamResponse:
    s = link.open_stream()
    try:
        s.send_open(open_msg)
        head = await asyncio.wait_for(s.open_msg, OPEN_TIMEOUT_S)
    except (StreamClosed, asyncio.TimeoutError):
        s.send_close(1011, "open failed")
        return web.json_response({"error": "space link stream failed"}, status=502)
    if _status(head) != 101:
        s.send_close(0, "refused")
        return web.json_response({"error": "upstream websocket refused",
                                  "status": _status(head)}, status=502)
    proto = head.get("protocol")
    if proto not in open_msg.get("protocols", []):
        proto = None
    ws = web.WebSocketResponse(compress=False, max_msg_size=WS_MAX_MSG,
                               protocols=(proto,) if proto else ())
    await ws.prepare(request)

    async def down() -> None:  # link -> client
        while True:
            m = await s.recv_message(WS_MAX_MSG)
            if m is None:
                break
            flags, body = m
            if flags & P.TEXT:
                await ws.send_str(body.decode("utf-8", "replace"))
            else:
                await ws.send_bytes(body)
        info = s.close_info if isinstance(s.close_info, dict) else {}
        try:
            code = int(info.get("code") or 1000)
        except (TypeError, ValueError):
            code = 1011
        if code < 1000 or code > 4999:
            code = 1011
        await ws.close(code=code, message=str(info.get("reason", "")).encode()[:120])

    down_task = asyncio.ensure_future(down())
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                await s.send_data(msg.data.encode(), flags=P.TEXT, fin=True)
            elif msg.type == WSMsgType.BINARY:
                await s.send_data(msg.data, fin=True)
            else:
                break
    except StreamClosed:
        pass
    finally:
        if not s.closed:
            s.send_close(ws.close_code or 1000, "client closed")
        down_task.cancel()
        try:
            await down_task
        except (asyncio.CancelledError, Exception):  # noqa: BLE001
            pass
    return ws


# --- agent side -------------------------------------------------------------

def _agent_headers(raw: list, sim_origin: str, ws: bool) -> list[tuple[str, str]]:
    out = filter_request_headers(raw)
    if any(str(k).lower() == "origin" for k, _ in _header_items(raw)):
        out.append(("Origin", sim_origin))   # checked at the GSG, rewritten to the sim's own origin
    return out


def build_upstream(sim_base: str, msg: dict) -> tuple[URL | None, str | None]:
    """The URL the agent will request, or ``(None, reason)``. The allowlist is
    applied to the path the GSG sent AND re-checked on the final URL."""
    method = msg.get("method")
    websocket = msg.get("kind") == "ws"
    path = msg.get("path")
    query = msg.get("query") or ""
    if not isinstance(method, str) or not isinstance(path, str):
        return None, "malformed request"
    canonical, reason = check_route(method, path, websocket)
    if canonical is None:
        return None, reason
    if canonical != path:
        return None, "path not in canonical form"
    if not query_ok(query):
        return None, "malformed query"
    base = URL(sim_base)
    try:
        url = URL.build(scheme="ws" if websocket else "http", host=base.host, port=base.port,
                        path=canonical, query_string=query, encoded=True)
    except (TypeError, ValueError) as e:
        return None, f"bad upstream url: {type(e).__name__}"
    final, reason = check_route(method, url.raw_path, websocket)
    if final != canonical or url.path != normalise_path(url.raw_path) \
            or url.host != base.host or url.port != base.port or url.fragment:
        return None, reason or "upstream url differs from the checked path"
    return url, None


async def _refuse(s: Stream, status: int, reason: str) -> None:
    s.send_open({"status": status, "headers": [["Content-Type", "application/json"]]})
    await s.send_data(P.dumps({"error": "forbidden" if status == 403 else "bad request",
                               "reason": reason}), fin=True)


async def agent_serve_stream(s: Stream, msg: dict, session: aiohttp.ClientSession,
                             sim_base: str) -> None:
    """Handle a proxy stream opened by the GSG."""
    url, reason = build_upstream(sim_base, msg if isinstance(msg, dict) else {})
    if url is None:
        # Defence in depth: the GSG already enforces the allowlist.
        logger.warning(P.kv("agent_proxy_denied", path=str(msg.get("path"))[:200],
                            reason=reason))
        await _refuse(s, 403, str(reason))
        return
    sim_origin = str(URL(sim_base).origin())
    if msg.get("kind") == "ws":
        await _agent_ws(s, msg, session, url, sim_origin)
    else:
        await _agent_http(s, msg, session, url, sim_origin)


async def _agent_http(s: Stream, msg: dict, session: aiohttp.ClientSession, url: URL,
                      sim_origin: str) -> None:
    first = await s.recv()
    if first is None:
        return
    flags, payload = first
    data: Any
    if flags & P.FIN:
        data = payload or None
    else:
        async def body():
            total = len(payload)
            yield payload
            while True:
                item = await s.recv()
                if item is None:
                    raise StreamClosed(s.id)
                f, p = item
                total += len(p)
                if total > MAX_REQUEST_BODY:
                    raise StreamClosed(s.id)
                if p:
                    yield p
                if f & P.FIN:
                    return
        data = body()
    headers = _agent_headers(msg.get("headers") or [], sim_origin, ws=False)
    head_sent = False
    try:
        # ``session`` is created with auto_decompress=False and no total
        # timeout: bodies pass through byte-for-byte (gzip stays gzip).
        async with session.request(str(msg.get("method", "GET")), url, headers=headers,
                                   data=data, allow_redirects=False) as resp:
            raw = [(k.decode("latin-1"), v.decode("latin-1")) for k, v in resp.raw_headers]
            out_headers = [[k, v] for k, v in filter_response_headers(raw)]
            s.send_open({"status": resp.status, "headers": out_headers})
            head_sent = True
            async for chunk in resp.content.iter_chunked(P.CHUNK):
                await s.send_data(chunk)
            await s.send_data(b"", fin=True)
    except StreamClosed:
        return
    except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as e:
        if head_sent:
            s.send_close(1011, "upstream body failed")
        else:
            try:
                s.send_open({"status": 502, "headers": [["Content-Type", "application/json"]]})
                await s.send_data(P.dumps({"error": "simulator unreachable",
                                           "detail": type(e).__name__}), fin=True)
            except StreamClosed:
                pass


async def _agent_ws(s: Stream, msg: dict, session: aiohttp.ClientSession, url: URL,
                    sim_origin: str) -> None:
    headers = _agent_headers(msg.get("headers") or [], sim_origin, ws=True)
    protocols = tuple(p for p in (msg.get("protocols") or ())
                      if isinstance(p, str) and _HEADER_NAME_RE.fullmatch(p))[:8]
    try:
        ws = await session.ws_connect(url, headers=headers, protocols=protocols,
                                      compress=0, max_msg_size=WS_MAX_MSG, autoping=True)
    except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as e:
        status = getattr(e, "status", 502) or 502
        s.send_open({"status": status})
        return
    s.send_open({"status": 101, "protocol": ws.protocol})

    async def up() -> None:  # link -> sim
        while True:
            m = await s.recv_message(WS_MAX_MSG)
            if m is None:
                break
            flags, body = m
            if flags & P.TEXT:
                await ws.send_str(body.decode("utf-8", "replace"))
            else:
                await ws.send_bytes(body)
        await ws.close()

    up_task = asyncio.ensure_future(up())
    try:
        async for m in ws:
            if m.type == WSMsgType.TEXT:
                await s.send_data(m.data.encode(), flags=P.TEXT, fin=True)
            elif m.type == WSMsgType.BINARY:
                await s.send_data(m.data, fin=True)
            else:
                break
    except StreamClosed:
        pass
    finally:
        up_task.cancel()
        try:
            await up_task
        except (asyncio.CancelledError, Exception):  # noqa: BLE001
            pass
        if not ws.closed:
            await ws.close()
        if not s.closed:
            s.send_close(ws.close_code or 1000, "upstream closed")
